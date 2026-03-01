import pytest
from datetime import timedelta, datetime, time
from django.utils import timezone
from django.urls import reverse
from django.test import override_settings 
from rest_framework import status
from rest_framework.test import APIClient

from api.models import Patient, Appointment, Slot

pytestmark = pytest.mark.django_db


class TestPatientRegistrationFlow:

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_patient_standalone_signup_flow(self, mailoutbox):
        url = reverse("patient-list")
        
        patient_data = {
            "email": "new.patient@example.com",
            "username": "newpatient",
            "password": "Complex123!",
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-01",
            "blood_type": "O+",
            "allergies": "Pollen",
            "chronic_conditions": "Asthma",
            "current_medications": "Inhaler",
            "insurance": "Blue Cross",
            "weight": 75,
            "height": 180
        }
        
        api_client = APIClient()
        response = api_client.post(url, patient_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify patient created
        patient = Patient.objects.get(user__email="new.patient@example.com")
        assert patient.blood_type == "O+"
        assert patient.allergies == "Pollen"
        assert patient.weight == 75
        assert patient.height == 180
        
        # Verify user created and inactive
        user = patient.user
        assert not user.is_active
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        
        # Verify verification email sent
        assert len(mailoutbox) == 1
        email = mailoutbox[0]
        assert email.to == ["new.patient@example.com"]
        assert "Confirmation Email" in email.subject
        
        # Verify cannot login until verified
        login_url = reverse("login")
        login_response = api_client.post(login_url, {
            "email": "new.patient@example.com",
            "password": "Complex123!"
        }, format="json")
        assert login_response.status_code == status.HTTP_403_FORBIDDEN
        assert "E-mail not verified" in login_response.data["detail"]

    def test_patient_onboarding_existing_user_flow(self, user_factory):
        """Test onboarding an existing user as a patient"""
        # Create existing user without patient profile
        user = user_factory(is_active=True)
        api_client = APIClient()

        api_client.force_authenticate(user=user)
        
        url = reverse("patient-on-board")
        patient_data = {
            "blood_type": "A+",
            "allergies": "None",
            "chronic_conditions": "None",
            "current_medications": "None",
            "insurance": "Medicare",
            "weight": 70,
            "height": 175
        }
        
        response = api_client.post(url, patient_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify patient profile created
        patient = Patient.objects.get(user=user)
        assert patient.blood_type == "A+"
        assert patient.weight == 70
        
        # Try onboarding again - should fail
        response = api_client.post(url, patient_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Patient profile already exists" in response.data["detail"]

    def test_patient_onboarding_validation(self, user_factory):
        """Test validation during patient onboarding"""
        user = user_factory(is_active=True)
        api_client = APIClient()

        api_client.force_authenticate(user=user)
        
        url = reverse("patient-on-board")
        
        # Test invalid weight
        response = api_client.post(url, {
            "weight": -10,
            "height": 175
        }, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "greater than or equal to 0" in str(response.data).lower()
        
        # Test invalid height
        response = api_client.post(url, {
            "weight": 70,
            "height": -5
        }, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "greater than or equal to 0" in str(response.data).lower()

class TestPatientProfileFlow:
    """Test patient profile retrieval and updates"""

    def test_patient_retrieve_own_profile(self, patient_factory):
        """Test patient can retrieve their own profile"""
        patient = patient_factory(
            blood_type="B+",
            allergies="Dust",
            weight=80
        )
        api_client = APIClient()
        
        api_client.force_authenticate(user=patient.user)
        url = reverse("patient-detail", kwargs={"pk": patient.user.pk})
        
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        data = response.data
        assert data["user"]["firstName"] == patient.user.first_name
        assert data["user"]["lastName"] == patient.user.last_name
        assert data["user"]["email"] == patient.user.email
        assert data["bloodType"] == "B+"
        assert data["allergies"] == "Dust"
        assert data["weight"] == 80

    def test_patient_update_own_profile(self, patient_factory):
        """Test patient can update their own profile"""
        patient = patient_factory(
            blood_type="O+",
            allergies="None",
            weight=70
        )
        api_client = APIClient()
        
        api_client.force_authenticate(user=patient.user)
        
        # Test partial update (PATCH)
        url = reverse("patient-detail", kwargs={"pk": patient.user.pk})
        update_data = {
            "blood_type": "A+",
            "allergies": "Peanuts",
            "weight": 72
        }
        
        response = api_client.patch(url, update_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        patient.refresh_from_db()
        assert patient.blood_type == "A+"
        assert patient.allergies == "Peanuts"
        assert patient.weight == 72
        
        # Test updating user fields through patient endpoint
        user_update = {
            "user": {
                "first_name": "Updated",
                "last_name": "Name",
                "phone_number": "1234567890"
            }
        }
        
        response = api_client.patch(url, user_update, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        patient.user.refresh_from_db()
        assert patient.user.first_name == "Updated"
        assert patient.user.last_name == "Name"
        assert patient.user.phone_number == "1234567890"

    def test_patient_cannot_update_others_profile(self, patient_factory):
        """Test patient cannot update another patient's profile"""
        patient1 = patient_factory()
        patient2 = patient_factory()
        api_client = APIClient()
        
        api_client.force_authenticate(user=patient1.user)
        
        url = reverse("patient-detail", kwargs={"pk": patient2.user.pk})
        update_data = {"blood_type": "AB+"}
        
        response = api_client.patch(url, update_data, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_staff_can_list_all_patients(self, patient_factory, admin_staff_factory):
        """Test staff can view all patients"""
        # Create multiple patients
        patient_factory()
        patient_factory()
        patient_factory()
        api_client = APIClient()
        
        staff = admin_staff_factory()
        
        api_client.force_authenticate(user=staff.user)
        url = reverse("patient-list")
        
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        
        assert len(response.data) >= 3

    def test_patient_cannot_list_all_patients(self, patient_factory):
        """Test patient cannot list all patients"""
        patient = patient_factory()
        api_client = APIClient()
        
        api_client.force_authenticate(user=patient.user)
        url = reverse("patient-list")
        
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

class TestPatientAppointmentFlow:
    """Test patient appointment-related operations"""

    def test_patient_view_own_appointments(self, patient_factory, 
                                           appointment_factory, provider_factory):
        """Test patient can view their own appointments"""
        patient = patient_factory()
        provider = provider_factory()
        api_client = APIClient()

        base_time = timezone.now() + timedelta(days=1)
        
        # Create appointments for this patient
        app1 = appointment_factory(
            patient=patient,
            appointment_start_datetime_utc=base_time,
            appointment_end_datetime_utc=base_time + timedelta(minutes=30),
            healthcare_provider=provider,
            status=Appointment.Status.CONFIRMED
        )
        app2 = appointment_factory(
            patient=patient,
            appointment_start_datetime_utc=base_time + timedelta(days=1),
            appointment_end_datetime_utc=base_time + timedelta(days=1, minutes=30),
            healthcare_provider=provider,
            status=Appointment.Status.REQUESTED
        )
        
        # Create appointment for another patient
        other_patient = patient_factory()
        appointment_factory(
            patient=other_patient,
            healthcare_provider=provider
        )
        
        api_client.force_authenticate(user=patient.user)
        url = reverse("appointment-list")
        
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        
        # Should only see own appointments
        assert len(response.data) == 2
        appointment_ids = [app["id"] for app in response.data]
        assert app1.id in appointment_ids
        assert app2.id in appointment_ids

    def test_patient_view_single_appointment(self, patient_factory, 
                                             appointment_factory):
        """Test patient can view details of their own appointment"""
        patient = patient_factory()
        appointment = appointment_factory(patient=patient)
        api_client = APIClient()
        
        api_client.force_authenticate(user=patient.user)
        url = reverse("appointment-detail", kwargs={"pk": appointment.id})
        
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        
        # Verify appointment details (CamelCase)
        data = response.data
        assert data["id"] == appointment.id
        assert data["patient"]["user"]["firstName"] == patient.user.first_name
        assert data["status"] == appointment.status
        assert "provider" in data
        assert "location" in data

    def test_patient_cannot_view_others_appointment(self, patient_factory,
                                                    appointment_factory):
        """Test patient cannot view another patient's appointment"""
        patient1 = patient_factory()
        patient2 = patient_factory()
        api_client = APIClient()
        
        appointment = appointment_factory(patient=patient1)
        
        api_client.force_authenticate(user=patient2.user)
        url = reverse("appointment-detail", kwargs={"pk": appointment.id})
        
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_patient_book_appointment_with_free_slot(self, patient_factory,
                                                     provider_factory, slot_factory):
        """Test patient can book an appointment for a free slot"""
        patient = patient_factory()
        provider = provider_factory()
        hospital = provider.primary_hospital
        api_client = APIClient()
        
        # Create a free slot
        start_time = timezone.now() + timedelta(days=2, hours=10)
        end_time = start_time + timedelta(minutes=30)
        
        slot = slot_factory(
            healthcare_provider=provider,
            hospital=hospital,
            start=start_time,
            end=end_time,
            status=Slot.Status.FREE,
            appointment=None
        )
        
        api_client.force_authenticate(user=patient.user)
        url = reverse("appointment-list")
        
        appointment_data = {
            "provider": provider.pk,
            "location": hospital.id,
            "appointment_start_datetime_utc": start_time.isoformat(),
            "appointment_end_datetime_utc": end_time.isoformat(),
            "reason": "Regular checkup"
        }
        
        response = api_client.post(url, appointment_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify appointment created
        appointment_id = response.data["id"]
        appointment = Appointment.objects.get(id=appointment_id)
        assert appointment.patient == patient
        assert appointment.healthcare_provider == provider
        assert appointment.status == Appointment.Status.REQUESTED
        
        # Verify slot is now booked
        slot.refresh_from_db()
        assert slot.status == Slot.Status.BOOKED
        assert slot.appointment == appointment

    def test_patient_cannot_book_past_appointment(self, patient_factory,
                                                  provider_factory):
        """Test patient cannot book an appointment in the past"""
        patient = patient_factory()
        provider = provider_factory()
        api_client = APIClient()
        
        api_client.force_authenticate(user=patient.user)
        url = reverse("appointment-list")
        
        past_time = timezone.now() - timedelta(days=1)
        
        appointment_data = {
            "provider": provider.pk,
            "location": provider.primary_hospital.id,
            "appointment_start_datetime_utc": past_time.isoformat(),
            "appointment_end_datetime_utc": (past_time + timedelta(minutes=30)).isoformat(),
            "reason": "Should fail"
        }
        
        response = api_client.post(url, appointment_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "past" in str(response.data).lower()

    def test_patient_cannot_book_already_booked_slot(self, patient_factory,
                                                     provider_factory, slot_factory):
        """Test patient cannot book an already booked slot"""
        patient = patient_factory()
        provider = provider_factory()
        api_client = APIClient()
        hospital = provider.primary_hospital
        
        # Create booked slot
        slot = slot_factory(
            healthcare_provider=provider,
            hospital=hospital,
            status=Slot.Status.BOOKED
        )
        
        api_client.force_authenticate(user=patient.user)
        url = reverse("appointment-list")
        
        appointment_data = {
            "provider": provider.pk,
            "location": hospital.id,
            "appointment_start_datetime_utc": slot.start.isoformat(),
            "appointment_end_datetime_utc": slot.end.isoformat(),
            "reason": "Should fail"
        }
        
        response = api_client.post(url, appointment_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No available slot" in response.data["detail"]

    def test_patient_view_free_slots(self, patient_factory,
                                     provider_factory, slot_factory):
        """Test patient can view free slots for a provider"""
        patient = patient_factory()
        provider = provider_factory()
        api_client = APIClient()
        hospital = provider.primary_hospital
        
        # Create mix of free and booked slots
        base_date = timezone.now().date() + timedelta(days=3)
        
        # Free slots
        for hour in [9, 10, 11]:
            start = timezone.make_aware(
                datetime.combine(base_date, time(hour, 0))
            )
            slot_factory(
                healthcare_provider=provider,
                hospital=hospital,
                start=start,
                end=start + timedelta(minutes=30),
                status=Slot.Status.FREE,
                appointment=None
            )
        
        # Booked slot
        booked_start = timezone.make_aware(
            datetime.combine(base_date, time(14, 0))
        )
        slot_factory(
            healthcare_provider=provider,
            hospital=hospital,
            start=booked_start,
            end=booked_start + timedelta(minutes=30),
            status=Slot.Status.BOOKED
        )
        
        api_client.force_authenticate(user=patient.user)
        url = reverse("slot-free")
        
        params = {
            "provider": provider.pk,
            "date": base_date.isoformat()
        }
        
        response = api_client.get(url, params)
        assert response.status_code == status.HTTP_200_OK
        
        # Should only see 3 free slots
        assert len(response.data) == 3
        for slot in response.data:
            assert slot["status"] == Slot.Status.FREE

class TestPatientMedicalRecordFlow:
    """Test patient medical record viewing"""

    def test_patient_view_own_medical_records(self, patient_factory,
                                              medical_record_factory):
        """Test patient can view their own medical records"""
        patient = patient_factory()
        api_client = APIClient()
        
        # Create medical records for this patient
        record1 = medical_record_factory(patient=patient)
        record2 = medical_record_factory(patient=patient)
        
        # Create record for another patient
        other_patient = patient_factory()
        medical_record_factory(patient=other_patient)
        
        api_client.force_authenticate(user=patient.user)
        url = reverse("medical_record-list")
        
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        
        # Should only see own records
        assert len(response.data) == 2
        record_ids = [r["id"] for r in response.data]
        assert record1.id in record_ids
        assert record2.id in record_ids

    def test_patient_view_single_medical_record(self, patient_factory,
                                                medical_record_factory):
        """Test patient can view details of their own medical record"""
        patient = patient_factory()
        record = medical_record_factory(patient=patient)
        api_client = APIClient()
        
        api_client.force_authenticate(user=patient.user)
        url = reverse("medical_record-detail", kwargs={"pk": record.id})
        
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        
        # Verify record details (CamelCase)
        data = response.data
        assert data["id"] == record.id
        assert data["patientDetails"]["fullName"] == patient.user.get_full_name()
        assert data["diagnosis"] == record.diagnosis
        assert "providerDetails" in data
        assert "hospitalDetails" in data

    def test_patient_cannot_view_others_medical_record(self, patient_factory,
                                                       medical_record_factory):
        """Test patient cannot view another patient's medical record"""
        patient1 = patient_factory()
        patient2 = patient_factory()
        api_client = APIClient()
        
        record = medical_record_factory(patient=patient1)
        
        api_client.force_authenticate(user=patient2.user)
        url = reverse("medical_record-detail", kwargs={"pk": record.id})
        
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_patient_cannot_create_medical_record(self, patient_factory,
                                                  appointment_factory):
        """Test patient cannot create medical records (provider only)"""
        patient = patient_factory()
        appointment = appointment_factory(patient=patient)
        api_client = APIClient()
        
        api_client.force_authenticate(user=patient.user)
        url = reverse("medical_record-list")
        
        record_data = {
            "patient_id": patient.pk,
            "appointment_id": appointment.id,
            "hospital_id": appointment.location.id,
            "diagnosis": "Test diagnosis",
            "notes": "Test notes",
            "prescriptions": "Test prescriptions"
        }
        
        response = api_client.post(url, record_data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

class TestPatientValidationFlow:

    def test_patient_signup_duplicate_email(self, user_factory):
        """Test cannot signup with existing email"""
        user_factory(email="existing@example.com")
        api_client = APIClient()
        
        url = reverse("patient-list")
        patient_data = {
            "email": "existing@example.com",
            "username": "newuser",
            "password": "Complex123!",
            "first_name": "John",
            "last_name": "Doe"
        }
        
        response = api_client.post(url, patient_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email already exists" in str(response.data).lower()

    def test_patient_signup_missing_required_fields(self):
        """Test validation for missing required fields"""
        url = reverse("patient-list")
        api_client = APIClient()
        
        # Missing first_name
        response = api_client.post(url, {
            "email": "test@example.com",
            "username": "testuser",
            "password": "Complex123!",
            "last_name": "Doe"
        }, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Missing password
        response = api_client.post(url, {
            "email": "test@example.com",
            "username": "testuser",
            "first_name": "John",
            "last_name": "Doe"
        }, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_patient_me_endpoint(self, patient_factory):
        """Test /me endpoint for patient"""
        patient = patient_factory(
            blood_type="AB-",
            allergies="Shellfish"
        )
        api_client = APIClient()
        
        api_client.force_authenticate(user=patient.user)
        
        url = reverse("patient-me")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.data
        assert data["user"]["id"] == str(patient.user.id)
        assert data["bloodType"] == "AB-"
        assert data["allergies"] == "Shellfish"
        
        update_data = {
            "blood_type": "O+",
            "allergies": "Updated allergies"
        }
        response = api_client.patch(url, update_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        patient.refresh_from_db()
        assert patient.blood_type == "O+"
        assert patient.allergies == "Updated allergies"

    def test_patient_me_endpoint_no_profile(self, user_factory):
        """Test /me endpoint returns 404 for user without patient profile"""
        user = user_factory()
        api_client = APIClient()
        
        api_client.force_authenticate(user=user)
        url = reverse("patient-me")
        
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_patient_appointment_constraints(self, patient_factory,
                                             provider_factory, slot_factory):
        """Test database constraints for appointments"""
        patient = patient_factory()
        provider = provider_factory()
        hospital = provider.primary_hospital
        api_client = APIClient()
        
        start_time = timezone.now() + timedelta(days=2)
        slot = slot_factory(
            healthcare_provider=provider,
            hospital=hospital,
            start=start_time,
            end=start_time + timedelta(minutes=30),
            status=Slot.Status.FREE
        )
        
        api_client.force_authenticate(user=patient.user)
        url = reverse("appointment-list")
        
        appointment_data = {
            "provider": provider.pk,
            "patient": patient.pk,
            "location": hospital.id,
            "appointment_start_datetime_utc": slot.start.isoformat(),
            "appointment_end_datetime_utc": slot.end.isoformat(),
            "reason": "First booking"
        }
        
        response = api_client.post(url, appointment_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        
        # Try to book same slot again
        response = api_client.post(url, appointment_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "An appointment already exist at this time" in str(response.data)
        
        # Verify only one appointment created
        assert Appointment.objects.filter(
            patient=patient,
            healthcare_provider=provider,
            appointment_start_datetime_utc=slot.start
        ).count() == 1