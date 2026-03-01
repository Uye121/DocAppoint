import pytest
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from rest_framework.test import APIClient
from datetime import timedelta, datetime, time

from api.models import (
    HealthcareProvider,
    ProviderHospitalAssignment,
    Appointment,
    Slot
)


pytestmark = pytest.mark.django_db


class TestHealthcareProviderFlow:

    def test_provider_creation_and_onboarding_flow(self, authenticated_admin_client, 
                                                   speciality_factory, hospital_factory):
        """Test complete flow: staff creates provider -> provider manages profile"""
        speciality = speciality_factory()
        hospital = hospital_factory()
        api_client = APIClient()
        admin_client, _ = authenticated_admin_client()
        
        # Staff/admin creates new provider
        provider_create_url = reverse("provider-list")
        provider_data = {
            "email": "dr.smith@example.com",
            "username": "drsmith",
            "password": "ComplexPass123!",
            "first_name": "John",
            "last_name": "Smith",
            "speciality": speciality.id,
            "fees": "150.00",
            "address_line1": "123 Medical Center Dr",
            "city": "Boston",
            "state": "MA",
            "zip_code": "02115",
            "license_number": "MD123456",
            "about": "Experienced cardiologist",
            "education": "Harvard Medical School",
            "years_of_experience": 10,
            "primary_hospital": hospital.id
        }
        
        response = admin_client.post(provider_create_url, provider_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        print(response.data)
        
        provider_id = response.data["id"]
        provider = HealthcareProvider.objects.get(user_id=provider_id)
        
        # Verify provider created but inactive
        assert not provider.user.is_active
        assert provider.speciality == speciality
        assert provider.fees == 150.00
        
        # Activate provider in real flow via email verification
        provider.user.is_active = True
        provider.user.save()
        
        # Step 4: Provider logs in
        login_url = reverse("login")
        login_data = {
            "email": "dr.smith@example.com",
            "password": "ComplexPass123!"
        }
        response = api_client.post(login_url, login_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        access_token = response.data["access"]
        
        # Provider accesses their profile via /me endpoint
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        me_url = reverse("provider-me")
        
        response = api_client.get(me_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["user"]["email"] == "dr.smith@example.com"
        assert response.data["speciality"] == speciality.id
        
        # Provider updates their profile
        update_data = {
            "about": "Updated: 15 years experience in cardiology",
            "fees": "175.00"
        }
        response = api_client.patch(me_url, update_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        provider.refresh_from_db()
        assert provider.about == "Updated: 15 years experience in cardiology"
        assert provider.fees == 175.00

    def test_provider_hospital_affiliation_management(self, authenticated_admin_client, provider_factory, 
                                                      hospital_factory, user_factory):
        """Test managing provider's hospital affiliations"""
        provider = provider_factory()
        hospital1 = hospital_factory()
        hospital2 = hospital_factory()
        
        admin_client, _ = authenticated_admin_client()

        ProviderHospitalAssignment.objects.filter(
            healthcare_provider=provider
        ).delete()
        
        # Assign provider to hospitals
        assign_url = reverse("provider-assign-hospital", args=[provider.pk])
        
        response = admin_client.post(assign_url, {"hospital_id": hospital1.id}, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        response = admin_client.post(assign_url, {"hospital_id": hospital2.id}, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify hospital affiliations
        active_assignments = ProviderHospitalAssignment.objects.filter(
            healthcare_provider=provider,
            is_active=True
        )
        assert active_assignments.count() == 2
        
        # Get list of hospitals
        hospitals_url = reverse("provider-hospitals", args=[provider.pk])
        response = admin_client.get(hospitals_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        
        # Unassign one hospital
        unassign_url = reverse("provider-unassign-hospital", args=[provider.pk])
        response = admin_client.post(unassign_url, {"hospital_id": hospital1.id}, format="json")
        assert response.status_code == status.HTTP_200_OK

        # Verify only one assigned hospital left
        active_assignments = ProviderHospitalAssignment.objects.filter(
            healthcare_provider=provider,
            is_active=True
        )
        assert active_assignments.count() == 1
        assert active_assignments.first().hospital_id == hospital2.id

        response = admin_client.get(hospitals_url)
        assert len(response.data) == 1
        assert response.data[0]['id'] == hospital2.id

    def test_provider_slot_management_flow(self, authenticated_provider_client, 
                                           hospital_factory, authenticated_patient_client):
        """Test provider creates slots -> patient views free slots"""
        provider_client, provider = authenticated_provider_client()
        patient_client, _ = authenticated_patient_client()
        hospital = provider.primary_hospital or hospital_factory()
        
        slot_url = reverse("slot-list")
        base_date = timezone.now().date() + timedelta(days=3)
        created_slots = []
        
        # Create slots for 3 days, 3 slots per day
        for day_offset in range(3):
            current_date = base_date + timedelta(days=day_offset)
            for hour in [9, 10, 11]:
                start = timezone.make_aware(
                    datetime.combine(current_date, time(hour, 0))
                )
                end = start + timedelta(minutes=30)
                
                slot_data = {
                    "healthcare_provider": provider.user_id,
                    "hospital_id": hospital.id,
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "status": "FREE"
                }
                response = provider_client.post(slot_url, slot_data, format="json")
                assert response.status_code == status.HTTP_201_CREATED
                created_slots.append(response.data["id"])
        
        assert Slot.objects.filter(healthcare_provider=provider).count() == 9
        
        # views their slots for date range
        range_url = reverse("slot-range")
        params = {
            "provider": provider.user_id,
            "start_date": base_date.isoformat(),
            "end_date": (base_date + timedelta(days=2)).isoformat()
        }
        response = provider_client.get(range_url, params)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3
        
        # Patient views free slots
        free_slots_url = reverse("slot-free")
        params = {
            "provider": provider.user_id,
            "date": base_date.isoformat()
        }
        response = patient_client.get(free_slots_url, params)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3
        
        slot_id = created_slots[0]
        slot_detail_url = reverse("slot-detail", args=[slot_id])
        update_data = {"status": "BLOCKED"}
        response = provider_client.patch(slot_detail_url, update_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        # Verify slot is no longer free for patient
        response = patient_client.get(free_slots_url, params)
        assert len(response.data) == 2  # Only 2 free slots now

    def test_provider_schedule_generation_endpoint(self, authenticated_provider_client,
                                                   hospital_factory):
        """Test the custom generate-slots endpoint"""
        provider_client, provider = authenticated_provider_client()
        if not provider.primary_hospital:
            hospital = hospital_factory()
            provider.primary_hospital = hospital
            provider.save()

        generate_url = reverse("appointment-generate-slots")
        test_date = (timezone.now().date() + timedelta(days=7)).isoformat()
        
        generate_data = {
            "provider": provider.user_id,
            "date": test_date,
            "duration": 45,
            "opening": "08:00",
            "closing": "16:00"
        }
        
        response = provider_client.post(generate_url, generate_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["detail"] == "Slots generated."
        
        # Verify slots
        slots = Slot.objects.filter(
            healthcare_provider=provider,
            start__date=test_date
        )
        assert slots.count() > 0
        assert slots.first().duration == timedelta(minutes=45)

    def test_provider_search_and_filtering(self, authenticated_patient_client, provider_factory, 
                                        speciality_factory, hospital_factory):
        """Test public listing and filtering of providers"""
        patient_client, _ = authenticated_patient_client()

        cardio = speciality_factory(name="Cardiology")
        derma = speciality_factory(name="Dermatology")
        
        hospital_boston = hospital_factory(name="Boston General")
        hospital_nyc = hospital_factory(name="NYC Medical")
        
        provider1 = provider_factory(
            speciality=cardio,
            primary_hospital=hospital_boston,
            user__first_name="Cardio1",
            user__last_name="Doctor",
            fees=200.00
        )
        provider2 = provider_factory(
            speciality=cardio,
            primary_hospital=hospital_nyc,
            user__first_name="Cardio2",
            user__last_name="Doctor",
            fees=250.00
        )
        provider3 = provider_factory(
            speciality=derma,
            primary_hospital=hospital_boston,
            user__first_name="Derma1",
            user__last_name="Doctor",
            fees=150.00
        )
        
        for p in [provider1, provider2, provider3]:
            p.user.is_active = True
            p.user.save()
        
        # List all providers
        list_url = reverse("provider-list")
        response = patient_client.get(list_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3
        
        # Filter by speciality
        response = patient_client.get(list_url, {"speciality": cardio.id})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        
        # Search by name
        response = patient_client.get(list_url, {"search": "Cardio"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        
        # Get single provider details
        detail_url = reverse("provider-detail", args=[provider1.user_id])
        response = patient_client.get(detail_url)
        assert response.status_code == status.HTTP_200_OK
        print(response.data)
        assert response.data["specialityName"] == "Cardiology"
        assert response.data["user"]["firstName"] == "Cardio1"

    def test_provider_appointment_history(self, authenticated_provider_client,
                                          appointment_factory, patient_factory):
        """Test provider can view their appointment history"""
        provider_client, provider = authenticated_provider_client()
        
        patient1 = patient_factory()
        patient2 = patient_factory()
        
        # Past appointment (completed)
        past_appointment = appointment_factory(
            healthcare_provider=provider,
            patient=patient1,
            appointment_start_datetime_utc=timezone.now() - timedelta(days=5),
            appointment_end_datetime_utc=timezone.now() - timedelta(days=5, minutes=-30),
            status="COMPLETED"
        )
        
        # Future appointment (confirmed)
        future_appointment = appointment_factory(
            healthcare_provider=provider,
            patient=patient2,
            appointment_start_datetime_utc=timezone.now() + timedelta(days=3),
            appointment_end_datetime_utc=timezone.now() + timedelta(days=3, minutes=30),
            status="CONFIRMED"
        )
        
        # Create appointment for different provider
        other_provider_appointment = appointment_factory(
            patient=patient1,
            status="CONFIRMED"
        )
        
        # Get provider's appointments
        appointment_url = reverse("appointment-list")
        response = provider_client.get(appointment_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        
        appointment_ids = [a["id"] for a in response.data]
        assert past_appointment.id in appointment_ids
        assert future_appointment.id in appointment_ids
        assert other_provider_appointment.id not in appointment_ids
        
        # Filter by status
        response = provider_client.get(appointment_url, {"status": "COMPLETED"})
        assert len(response.data) == 1
        assert response.data[0]["id"] == past_appointment.id

    def test_provider_onboard_existing_user(self, authenticated_admin_client, user_factory, 
                                            speciality_factory, hospital_factory):
        """Test onboarding an existing user as a provider"""
        user = user_factory(is_active=True)
        admin_client, _ = authenticated_admin_client()
        
        speciality = speciality_factory()
        hospital = hospital_factory()
        
        # Admin onboards user as provider
        onboard_url = reverse("provider-onboard")
        onboard_data = {
            "user": user.id,
            "speciality": speciality.id,
            "education": "Stanford Medical School",
            "years_of_experience": 8,
            "about": "Experienced physician",
            "fees": "180.00",
            "address_line1": "456 Health Ave",
            "city": "San Francisco",
            "state": "CA",
            "zip_code": "94105",
            "license_number": "CA789012",
            "primary_hospital": hospital.id
        }
        
        response = admin_client.post(onboard_url, onboard_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        
        user.refresh_from_db()
        assert hasattr(user, "provider")
        assert user.provider.speciality == speciality
        assert user.provider.fees == 180.00
        
        # Fail to onboard the same user
        response = admin_client.post(onboard_url, onboard_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Provider profile already exists" in str(response.data)

class TestHealthcareProviderValidation:
    """Test validation rules for healthcare providers"""

    def test_provider_creation_validation(self, authenticated_admin_client, 
                                          speciality_factory, hospital_factory):
        """Test validation errors during provider creation"""
        admin_client, _ = authenticated_admin_client()
        speciality = speciality_factory()
        hospital = hospital_factory()
        
        url = reverse("provider-list")
        
        # Test invalid fees (<= 0)
        invalid_fees_data = {
            "email": "dr.invalid@example.com",
            "username": "drinvalid",
            "password": "ComplexPass123!",
            "first_name": "Invalid",
            "last_name": "Doctor",
            "speciality": speciality.id,
            "fees": "-50.00",  # Invalid
            "address_line1": "123 Medical Center Dr",
            "city": "Boston",
            "state": "MA",
            "zip_code": "02115",
            "license_number": "MD123456",
            "about": "Test",
            "primary_hospital": hospital.id
        }
        
        response = admin_client.post(url, invalid_fees_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "fees" in str(response.data).lower()
        
        # Test invalid license format
        invalid_license_data = {
            "email": "dr.license@example.com",
            "username": "drlicense",
            "password": "ComplexPass123!",
            "first_name": "License",
            "last_name": "Doctor",
            "speciality": speciality.id,
            "fees": "150.00",
            "address_line1": "123 Medical Center Dr",
            "city": "Boston",
            "state": "MA",
            "zip_code": "02115",
            "license_number": "abc",  # Too short
            "about": "Test",
            "primary_hospital": hospital.id
        }
        
        response = admin_client.post(url, invalid_license_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "license" in str(response.data).lower()
        
        # Test missing speciality
        missing_speciality_data = {
            "email": "dr.missing@example.com",
            "username": "drmissing",
            "password": "ComplexPass123!",
            "first_name": "Missing",
            "last_name": "Doctor",
            # speciality missing
            "fees": "150.00",
            "address_line1": "123 Medical Center Dr",
            "city": "Boston",
            "state": "MA",
            "zip_code": "02115",
            "license_number": "MD123456",
            "about": "Test",
            "primary_hospital": hospital.id
        }
        
        response = admin_client.post(url, missing_speciality_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "speciality" in str(response.data).lower()

class TestHealthcareProviderProfileAccess:
    """Test access control for provider profiles"""

    def test_provider_cannot_update_others_profile(self, provider_factory, 
                                                   authenticated_provider_client):
        """Test provider cannot update another provider's profile"""
        provider2 = provider_factory()
        
        client, _ = authenticated_provider_client()
        
        # Try to update provider2's profile via detail URL
        url = reverse("provider-detail", kwargs={"pk": provider2.user.pk})
        update_data = {"about": "Hacked!"}
        
        response = client.patch(url, update_data, format="json")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Verify provider2's profile unchanged
        provider2.refresh_from_db()
        assert provider2.about != "Hacked!"

    def test_provider_me_endpoint_no_profile(self, authenticated_user_client):
        """Test /me endpoint returns 404 for user without provider profile"""
        user_client, _ = authenticated_user_client()
        
        url = reverse("provider-me")
        response = user_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

class TestHealthcareProviderSlotValidation:
    """Test slot management validation rules"""

    def test_provider_cannot_create_past_slot(self, authenticated_provider_client):
        """Test provider cannot create slots in the past"""
        provider_client, provider = authenticated_provider_client()
        hospital = provider.primary_hospital
        
        url = reverse("slot-list")
        
        # Past time
        past_start = timezone.now() - timedelta(days=1)
        past_end = past_start + timedelta(minutes=30)
        
        slot_data = {
            "healthcare_provider": provider.user_id,
            "hospital_id": hospital.id,
            "start": past_start.isoformat(),
            "end": past_end.isoformat(),
            "status": "FREE"
        }
        
        response = provider_client.post(url, slot_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "past" in str(response.data).lower()

    def test_provider_cannot_create_slot_with_end_before_start(self, authenticated_provider_client):
        """Test validation for end time after start time"""
        provider_client, provider = authenticated_provider_client()
        hospital = provider.primary_hospital
        
        url = reverse("slot-list")
        
        future_date = timezone.now() + timedelta(days=3)
        
        # End before start
        slot_data = {
            "healthcare_provider": provider.user_id,
            "hospital_id": hospital.id,
            "start": future_date.isoformat(),
            "end": (future_date - timedelta(minutes=30)).isoformat(),  # Earlier
            "status": "FREE"
        }
        
        response = provider_client.post(url, slot_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "after start" in str(response.data).lower() or "end" in str(response.data).lower()

    def test_provider_cannot_duplicate_slot(self, authenticated_provider_client):
        """Test unique constraint for provider + start time"""
        provider_client, provider = authenticated_provider_client()
        hospital = provider.primary_hospital
        
        url = reverse("slot-list")
        
        start_time = timezone.now() + timedelta(days=3, hours=10)
        end_time = start_time + timedelta(minutes=30)
        
        # First slot
        slot_data = {
            "healthcare_provider": provider.user_id,
            "hospital_id": hospital.id,
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
            "status": "FREE"
        }
        
        response = provider_client.post(url, slot_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        
        # Duplicate slot
        response = provider_client.post(url, slot_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestHealthcareProviderAppointmentManagement:
    """Test provider's ability to manage appointments"""

    def test_provider_confirm_appointment(self, authenticated_provider_client,
                                        authenticated_patient_client, slot_factory):
        """Test provider can confirm a requested appointment"""
        provider_client, provider = authenticated_provider_client()
        patient_client, patient = authenticated_patient_client()
        hospital = provider.primary_hospital
        
        # Create a free slot
        start_time = timezone.now() + timedelta(days=3)
        end_time = start_time + timedelta(minutes=30)
        
        slot = slot_factory(
            healthcare_provider=provider,
            hospital=hospital,
            start=start_time,
            end=end_time,
            status=Slot.Status.FREE,
            appointment=None
        )
        
        # Patient books appointment
        appointment_url = reverse("appointment-list")
        appointment_data = {
            "patient": patient.pk,
            "provider": provider.pk,
            "location": hospital.id,
            "appointment_start_datetime_utc": start_time.isoformat(),
            "appointment_end_datetime_utc": end_time.isoformat(),
            "reason": "Checkup"
        }
        
        response = patient_client.post(appointment_url, appointment_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        appointment_id = response.data["id"]
        
        # Provider confirms
        set_status_url = reverse("appointment-set-status", args=[appointment_id])
        response = provider_client.post(set_status_url, {"status": "CONFIRMED"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        slot.refresh_from_db()
        assert slot.status == Slot.Status.BOOKED

    def test_provider_cancel_appointment(self, authenticated_provider_client,
                                         appointment_factory, patient_factory, slot_factory):
        """Test provider can cancel an appointment"""
        provider_client, provider = authenticated_provider_client()
        patient = patient_factory()
        hospital = provider.primary_hospital
        
        # Create slot and appointment
        start_time = timezone.now() + timedelta(days=3)
        end_time = start_time + timedelta(minutes=30)
        
        slot = slot_factory(
            healthcare_provider=provider,
            hospital=hospital,
            start=start_time,
            end=end_time,
            status=Slot.Status.BOOKED
        )
        
        appointment = appointment_factory(
            healthcare_provider=provider,
            patient=patient,
            appointment_start_datetime_utc=start_time,
            appointment_end_datetime_utc=end_time,
            status="CONFIRMED"
        )
        
        # Link slot to appointment
        slot.appointment = appointment
        slot.save()
        
        # Cancel appointment
        set_status_url = reverse("appointment-set-status", args=[appointment.id])
        response = provider_client.post(set_status_url, {"status": "CANCELLED"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        appointment.refresh_from_db()
        assert appointment.status == "CANCELLED"
        assert appointment.cancelled_at is not None
        
        # Verify slot is freed
        slot.refresh_from_db()
        assert slot.status == Slot.Status.FREE
        assert slot.appointment is None

    def test_provider_reschedule_appointment(self, authenticated_provider_client,
                                             appointment_factory, patient_factory, slot_factory,
                                             authenticated_patient_client):
        """Test provider can reschedule an appointment"""
        provider_client, provider = authenticated_provider_client()
        patient_client, patient = authenticated_patient_client()
        hospital = provider.primary_hospital
        
        # Create original slot and appointment
        original_start = timezone.now() + timedelta(hours=10)
        original_end = original_start + timedelta(minutes=30)
        
        original_slot = slot_factory(
            healthcare_provider=provider,
            hospital=hospital,
            start=original_start,
            end=original_end,
            status=Slot.Status.FREE,
            appointment=None
        )
        
        appointment_url = reverse("appointment-list")
        appointment_data = {
            "patient": patient.pk,
            "provider": provider.pk,
            "location": hospital.id,
            "appointment_start_datetime_utc": original_start.isoformat(),
            "appointment_end_datetime_utc": original_end.isoformat(),
            "reason": "Initial checkup"
        }

        response = patient_client.post(appointment_url, appointment_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        appointment_id = response.data["id"]

        # Verify original slot is now booked
        original_slot.refresh_from_db()
        assert original_slot.status == Slot.Status.BOOKED
        assert original_slot.appointment_id == appointment_id
            
        # Provider confirms the appointment (optional step)
        set_status_url = reverse("appointment-set-status", args=[appointment_id])
        response = provider_client.post(set_status_url, {"status": "CONFIRMED"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        # Create new free slot for rescheduling
        new_start = timezone.now() + timedelta(days=4, hours=14)
        new_end = new_start + timedelta(minutes=30)
        
        new_slot = slot_factory(
            healthcare_provider=provider,
            hospital=hospital,
            start=new_start,
            end=new_end,
            status=Slot.Status.FREE,
            appointment=None
        )
        
        # Provider reschedules the appointment
        reschedule_data = {
            "status": "RESCHEDULED",
            "new_start_datetime_utc": new_start.isoformat(),
            "new_end_datetime_utc": new_end.isoformat()
        }
        
        response = provider_client.post(set_status_url, reschedule_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        # Verify appointment updated
        appointment = Appointment.objects.get(id=appointment_id)
        assert appointment.status == "RESCHEDULED"
        assert appointment.appointment_start_datetime_utc == new_start
        assert appointment.appointment_end_datetime_utc == new_end
        
        # Verify original slot freed
        original_slot.refresh_from_db()
        assert original_slot.status == Slot.Status.FREE
        assert original_slot.appointment is None
        
        # Verify new slot booked
        new_slot.refresh_from_db()
        assert new_slot.status == Slot.Status.BOOKED
        assert new_slot.appointment_id == appointment_id
        
        # Verify appointment has correct slot relationship
        assert hasattr(appointment, 'slot')
        assert appointment.slot == new_slot

class TestHealthcareProviderEdgeCases:
    """Test edge cases for healthcare providers"""

    def test_provider_invalid_status_transitions(self, authenticated_provider_client,
                                                 authenticated_patient_client,
                                                 slot_factory):
        """Test invalid appointment status transitions"""
        provider_client, provider = authenticated_provider_client()
        patient_client, patient = authenticated_patient_client()
        hospital = provider.primary_hospital
        
        start_time = timezone.now() + timedelta(days=3)
        end_time = start_time + timedelta(minutes=30)
        
        slot = slot_factory(
            healthcare_provider=provider,
            hospital=hospital,
            start=start_time,
            end=end_time,
            status=Slot.Status.FREE,
            appointment=None
        )
        
        appointment_url = reverse("appointment-list")
        appointment_data = {
            "patient": patient.pk,
            "provider": provider.pk,
            "location": hospital.id,
            "appointment_start_datetime_utc": start_time.isoformat(),
            "appointment_end_datetime_utc": end_time.isoformat(),
            "reason": "Test appointment"
        }
        
        response = patient_client.post(appointment_url, appointment_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        appointment_id = response.data["id"]
        
        set_status_url = reverse("appointment-set-status", args=[appointment_id])
        
        # Invalid going from REQUESTED to RESCHEDULED due to missing time
        response = provider_client.post(set_status_url, {"status": "RESCHEDULED"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Update to CONFIRMED
        response = provider_client.post(set_status_url, {"status": "CONFIRMED"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        # Verify slot is now booked
        slot.refresh_from_db()
        assert slot.status == Slot.Status.BOOKED
        
        # Invalid going from CONFIRMED to REQUESTED
        response = provider_client.post(set_status_url, {"status": "REQUESTED"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_provider_reschedule_to_unavailable_slot(self, authenticated_provider_client,
                                                    authenticated_patient_client, slot_factory):
        """Test reschedule fails if requested slot is not free"""
        provider_client, provider = authenticated_provider_client()
        patient_client, patient = authenticated_patient_client()
        hospital = provider.primary_hospital
        
        original_start = timezone.now() + timedelta(days=3)
        original_end = original_start + timedelta(minutes=30)
        
        original_slot = slot_factory(
            healthcare_provider=provider,
            hospital=hospital,
            start=original_start,
            end=original_end,
            status=Slot.Status.FREE,
            appointment=None
        )
        
        # Patient books appointment via API
        appointment_url = reverse("appointment-list")
        appointment_data = {
            "patient": patient.pk,
            "provider": provider.pk,
            "location": hospital.id,
            "appointment_start_datetime_utc": original_start.isoformat(),
            "appointment_end_datetime_utc": original_end.isoformat(),
            "reason": "Original appointment"
        }
        
        response = patient_client.post(appointment_url, appointment_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        appointment_id = response.data["id"]
        
        # Refresh slot and check status
        original_slot.refresh_from_db()        
        assert original_slot.status == Slot.Status.BOOKED, f"Slot status is {original_slot.status}, expected BOOKED"
        
        # Provider confirms the appointment
        set_status_url = reverse("appointment-set-status", args=[appointment_id])
        response = provider_client.post(set_status_url, {"status": "CONFIRMED"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        # Try to reschedule to a time with NO slot
        new_start = timezone.now() + timedelta(days=4, hours=14)
        new_end = new_start + timedelta(minutes=30)
        
        reschedule_data = {
            "status": "RESCHEDULED",
            "new_start_datetime_utc": new_start.isoformat(),
            "new_end_datetime_utc": new_end.isoformat()
        }
        
        response = provider_client.post(set_status_url, reschedule_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST