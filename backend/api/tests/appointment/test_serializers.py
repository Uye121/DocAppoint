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
                "hospital_id": h.pk,
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
                "hospital_id": h.pk,
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
                "hospital_id": h.pk,
                "start": past,
                "end": past + timedelta(minutes=30),
                "status": "FREE",
            }
        )
        assert not s.is_valid()
        assert "Cannot create/modify a slot in the past." in str(s.errors["end"])


class TestAppointmentSerializers:
    @pytest.fixture
    def data(
        self,
        provider_factory,
        patient_factory,
        hospital_factory,
        user_factory,
        admin_staff_factory,
    ):
        a = admin_staff_factory()
        h = hospital_factory()
        provider = provider_factory()
        user = user_factory(email="user@test.com")
        patient = patient_factory(user=user)
        assignment = ProviderHospitalAssignment.objects.create(
            healthcare_provider=provider,
            hospital=h,
            created_by=a.user,
            updated_by=a.user,
        )
        now = timezone.now()
        return {
            "patient": patient,
            "provider": provider,
            "hospital": h,
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
            location=data["hospital"],
            reason="Check-up",
        )
        s = AppointmentListSerializer(instance=appt)

        assert s.data["status"] == "REQUESTED"
        assert (
            s.data["patientName"]
            == f"{data['patient'].user.first_name} {data['patient'].user.last_name}"
        )
        assert s.data["hospital"]["id"] == data["hospital"].id
        assert s.data["hospital"]["address"] == data["hospital"].address

    def test_appointment_detail_serializer(self, data):
        appt = Appointment.objects.create(
            patient=data["patient"],
            healthcare_provider=data["provider"],
            appointment_start_datetime_utc=data["start"],
            appointment_end_datetime_utc=data["end"],
            location=data["hospital"],
            reason="Detail",
        )
        s = AppointmentDetailSerializer(instance=appt)
        assert s.data["reason"] == "Detail"
        assert "status" in s.data

    def test_appointment_create_serializer_valid(self, data):
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(minutes=30)
        s = AppointmentCreateSerializer(
            data={
                "patient": data["patient"].pk,
                "provider": data["provider"].pk,
                "appointment_start_datetime_utc": start,
                "appointment_end_datetime_utc": end,
                "location": data["hospital"].pk,
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
                "location": data["hospital"].pk,
                "reason": "Past",
            }
        )
        assert not s.is_valid()
        assert "Cannot schedule an appointment in the past." in str(
            s.errors["appointment_start_datetime_utc"]
        )

    def test_create_serializer_end_before_start(self, data):
        start = timezone.now() + timedelta(hours=1)
        end = start - timedelta(minutes=1)
        s = AppointmentCreateSerializer(
            data={
                "patient": data["patient"].pk,
                "provider": data["provider"].pk,
                "appointment_start_datetime_utc": start,
                "appointment_end_datetime_utc": end,
                "location": data["hospital"].pk,
                "reason": "Bad",
            }
        )
        assert not s.is_valid()
        assert "End must be after start." in str(
            s.errors["appointment_end_datetime_utc"]
        )
