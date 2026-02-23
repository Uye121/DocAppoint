import pytest
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from rest_framework.test import APIClient
from datetime import timedelta, datetime, time

from api.models import HealthcareProvider, ProviderHospitalAssignment, Speciality, Slot


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