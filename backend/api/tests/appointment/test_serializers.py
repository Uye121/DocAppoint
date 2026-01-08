import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

from api.models import (
    Appointment,
    ProviderHospitalAssignment,
)
from ...serializers import (
    SlotSerializer,
    AppointmentListSerializer,
    AppointmentDetailSerializer,
    AppointmentCreateSerializer,
)

User = get_user_model()
pytestmark = pytest.mark.django_db(transaction=True)

class TestSlotSerializer:
    def test_valid_slot(self, provider_factory, hospital_factory):
        prov = provider_factory()
        h = hospital_factory()
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(minutes=30)
        ser = SlotSerializer(
            data={
                "healthcare_provider": prov.pk,
                "hospital": h.pk,
                "start": start,
                "end": end,
                "status": "FREE",
            }
        )
        assert ser.is_valid(), ser.errors
        slot = ser.save()
        assert slot.duration == timedelta(minutes=30)

    def test_end_before_start(self, provider_factory, hospital_factory):
        prov = provider_factory()
        h = hospital_factory()
        start = timezone.now() + timedelta(hours=1)
        s = SlotSerializer(
            data={
                "healthcare_provider": prov.pk,
                "hospital": h.pk,
                "start": start,
                "end": start - timedelta(minutes=1),
                "status": "FREE",
            }
        )
        assert not s.is_valid()
        assert "End time must be after start time." in str(s.errors["end"])

    def test_past_slot_blocked(self, provider_factory, hospital_factory):
        prov = provider_factory()
        h = hospital_factory()
        past = timezone.now() - timedelta(hours=2)
        s = SlotSerializer(
            data={
                "healthcare_provider": prov.pk,
                "hospital": h.pk,
                "start": past,
                "end": past + timedelta(minutes=30),
                "status": "FREE",
            }
        )
        assert not s.is_valid()
        assert "Cannot create/modify a slot in the past." in str(s.errors["end"])

class TestAppointmentSerializers:
    @pytest.fixture
    def data(self, provider_factory, patient_factory, hospital_factory, user_factory):
        h = hospital_factory()
        provider = provider_factory()
        user = user_factory(email="user@test.com")
        patient = patient_factory(user=user)
        assignment = ProviderHospitalAssignment.objects.create(healthcare_provider=provider, hospital=h)
        now = timezone.now()
        return {
            "patient": patient,
            "provider": provider,
            "assignment": assignment,
            "start": now + timedelta(hours=1),
            "end": now + timedelta(hours=2),
        }

    def test_appointment_list_serializer(self, data):
        appt = Appointment.objects.create(
            patient=data["patient"],
            healthcare_provider=data["provider"],
            appointment_start_datetime_utc=data["start"],
            appointment_end_datetime_utc=data["end"],
            location=data["assignment"],
            reason="Check-up",
        )
        s = AppointmentListSerializer(instance=appt)
        assert s.data["status"] == "REQUESTED"
        assert s.data["patient"]["user"]["email"] == "user@test.com"

    def test_appointment_detail_serializer(self, data):
        appt = Appointment.objects.create(
            patient=data["patient"],
            healthcare_provider=data["provider"],
            appointment_start_datetime_utc=data["start"],
            appointment_end_datetime_utc=data["end"],
            location=data["assignment"],
            reason="Detail",
        )
        s = AppointmentDetailSerializer(instance=appt)
        assert s.data["reason"] == "Detail"
        assert "created_at" in s.data

    def test_appointment_create_serializer_valid(self, data):
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(minutes=30)
        s = AppointmentCreateSerializer(
            data={
                "patient": data["patient"].pk,
                "provider": data["provider"].pk,
                "appointment_start_datetime_utc": start,
                "appointment_end_datetime_utc": end,
                "location": data["assignment"].pk,
                "reason": "New",
            }
        )
        assert s.is_valid(), s.errors
        appt = s.save()
        assert appt.reason == "New"
        assert appt.patient == data["patient"]

    def test_create_serializer_past_start_blocked(self, data):
        start = timezone.now() - timedelta(hours=1)
        end = start + timedelta(minutes=30)
        s = AppointmentCreateSerializer(
            data={
                "healthcare_provider": data["provider"].pk,
                "appointment_start_datetime_utc": start,
                "appointment_end_datetime_utc": end,
                "location": data["assignment"].pk,
                "reason": "Past",
            }
        )
        assert not s.is_valid()
        assert "Cannot schedule an appointment in the past." in str(s.errors["appointment_start_datetime_utc"])

    def test_create_serializer_end_before_start(self, data):
        start = timezone.now() + timedelta(hours=1)
        end = start - timedelta(minutes=1)
        s = AppointmentCreateSerializer(
            data={
                "patient": data["patient"].pk,
                "provider": data["provider"].pk,
                "appointment_start_datetime_utc": start,
                "appointment_end_datetime_utc": end,
                "location": data["assignment"].pk,
                "reason": "Bad",
            }
        )
        assert not s.is_valid()
        assert "End must be after start." in str(s.errors["appointment_end_datetime_utc"])