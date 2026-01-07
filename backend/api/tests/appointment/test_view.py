import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from ...models import (
    Appointment,
    Slot,
    HealthcareProvider,
    Hospital,
    ProviderHospitalAssignment,
    Patient,
    Speciality,
)

User = get_user_model()
pytestmark = pytest.mark.django_db

class TestAppointmentViewSet:
    url = "/api/appointment/"

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def data(self, hospital_factory, provider_factory, patient_factory):
        h = hospital_factory()
        provider = provider_factory()
        patient = patient_factory()
        assignment = ProviderHospitalAssignment.objects.create(
            provider=provider, hospital=h
        )
        now = timezone.now()
        return {
            "patient": patient,
            "provider": provider,
            "assignment": assignment,
            "start": now + timedelta(hours=1),
            "end": now + timedelta(hours=2),
        }

    # --------------- auth / listing ---------------
    def test_patient_view_own_appointments(self, api_client, data):
        api_client.force_authenticate(user=data["patient"].user)
        Appointment.objects.create(
            patient=data["patient"],
            healthcare_provider=data["provider"],
            appointment_start_datetime_utc=data["start"],
            appointment_end_datetime_utc=data["end"],
            location=data["assignment"],
            reason="Mine",
        )
        res = api_client.get(self.url)
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 1
        assert res.data[0]["reason"] == "Mine"

    def test_provider_sees_own_appointments(self, api_client, data):
        api_client.force_authenticate(user=data["provider"].user)
        Appointment.objects.create(
            patient=data["patient"],
            healthcare_provider=data["provider"],
            appointment_start_datetime_utc=data["start"],
            appointment_end_datetime_utc=data["end"],
            location=data["assignment"],
            reason="Provider view",
        )
        res = api_client.get(self.url)
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 1

    def test_anonymous_denied(self, api_client):
        res = api_client.get(self.url)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    # --------------- creation ---------------
    def test_patient_can_book_self(self, api_client, data):
        api_client.force_authenticate(user=data["patient"].user)
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(minutes=30)
        payload = {
            "patient": data["patient"].pk,
            "healthcare_provider": data["provider"].pk,
            "appointment_start_datetime_utc": start.isoformat(),
            "appointment_end_datetime_utc": end.isoformat(),
            "location": data["assignment"].pk,
            "reason": "Check-up",
        }
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        assert Appointment.objects.count() == 1
        appt = Appointment.objects.first()
        assert appt.patient == data["patient"]

    def test_provider_can_book_for_patient(self, api_client, data):
        api_client.force_authenticate(user=data["provider"].user)
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(minutes=30)
        payload = {
            "patient": data["patient"].pk,
            "healthcare_provider": data["provider"].pk,
            "appointment_start_datetime_utc": start.isoformat(),
            "appointment_end_datetime_utc": end.isoformat(),
            "location": data["assignment"].pk,
            "reason": "Provider booked",
        }
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        appt = Appointment.objects.first()
        assert appt.patient == data["patient"]

    def test_provider_book_patient_required(self, api_client, data):
        api_client.force_authenticate(user=data["provider"].user)
        start = timezone.now() + timedelta(hours=1)
        payload = {
            "healthcare_provider": data["provider"].pk,
            "appointment_start_datetime_utc": start.isoformat(),
            "appointment_end_datetime_utc": start + timedelta(minutes=30),
            "location": data["assignment"].pk,
            "reason": "No patient",
        }
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "This field is required." in res.data["patient"][0]

    def test_past_start_blocked(self, api_client, data):
        api_client.force_authenticate(user=data["patient"].user)
        past = timezone.now() - timedelta(minutes=5)
        payload = {
            "healthcare_provider": data["provider"].pk,
            "appointment_start_datetime_utc": past.isoformat(),
            "appointment_end_datetime_utc": past + timedelta(minutes=30),
            "location": data["assignment"].pk,
            "reason": "Past",
        }
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot schedule an appointment in the past." in res.data["appointment_start_datetime_utc"][0]

class TestSlotViewSet:
    url = "/api/slot/"

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def provider(self, provider_factory):
        return provider_factory()

    def test_provider_sees_own_slots(self, api_client, provider):
        api_client.force_authenticate(user=provider.user)
        tomorrow = timezone.now().date() + timedelta(days=1)
        slot = Slot.objects.create(
            provider=provider,
            hospital=provider.primary_hospital,
            start=timezone.make_aware(timezone.datetime.combine(tomorrow, timezone.datetime.min.time())) + timedelta(hours=9),
            end=timezone.make_aware(timezone.datetime.combine(tomorrow, timezone.datetime.min.time())) + timedelta(hours=10),
            status=Slot.Status.FREE,
        )
        res = api_client.get(self.url)
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 1
        assert res.data[0]["id"] == slot.id

    def test_provider_can_create_slot(self, api_client, provider):
        api_client.force_authenticate(user=provider.user)
        tomorrow = timezone.now().date() + timedelta(days=1)
        payload = {
            "provider": provider.pk,
            "hospital": provider.primary_hospital.pk,
            "start": timezone.make_aware(
                timezone.datetime.combine(tomorrow, timezone.datetime.min.time()) + timedelta(hours=9)
            ).isoformat(),
            "end": timezone.make_aware(
                timezone.datetime.combine(tomorrow, timezone.datetime.min.time()) + timedelta(hours=10)
            ).isoformat(),
            "status": "FREE",
        }
        res = api_client.post(self.url, payload, format="json")
        print(res.data)
        assert res.status_code == status.HTTP_201_CREATED
        assert Slot.objects.count() == 1
        slot = Slot.objects.first()
        assert slot.provider == provider

    def test_free_slots_action(self, api_client, provider):
        api_client.force_authenticate(user=provider.user)
        tomorrow = timezone.now().date() + timedelta(days=1)
        Slot.objects.create(
            provider=provider,
            hospital=provider.primary_hospital,
            start=timezone.make_aware(timezone.datetime.combine(tomorrow, timezone.datetime.min.time())) + timedelta(hours=9),
            end=timezone.make_aware(timezone.datetime.combine(tomorrow, timezone.datetime.min.time())) + timedelta(hours=10),
            status=Slot.Status.FREE,
        )
        Slot.objects.create(
            provider=provider,
            hospital=provider.primary_hospital,
            start=timezone.make_aware(timezone.datetime.combine(tomorrow, timezone.datetime.min.time())) + timedelta(hours=10),
            end=timezone.make_aware(timezone.datetime.combine(tomorrow, timezone.datetime.min.time())) + timedelta(hours=11),
            status=Slot.Status.BOOKED,
        )
        res = api_client.get(self.url + "free/", {"date": tomorrow.isoformat()})
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 1
