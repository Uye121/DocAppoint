import pytest
from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model

from api.models import (
    Appointment,
    Slot,
    ProviderHospitalAssignment,
)

User = get_user_model()
pytestmark = pytest.mark.django_db(transaction=True)

class TestAppointmentModel:
    @pytest.fixture
    def data(self, patient_factory, provider_factory, hospital_factory):
        h = hospital_factory()
        provider = provider_factory()
        provider.user.is_active = True
        provider.user.save(update_fields=["is_active"])

        patient = patient_factory()
        patient.user.is_active = True
        patient.user.save(update_fields=["is_active"])

        assignment = ProviderHospitalAssignment.objects.create(
            healthcare_provider=provider, hospital=h
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

    def test_create_appointment(self, data):
        appt = Appointment.objects.create(
            patient=data["patient"],
            healthcare_provider=data["provider"],
            appointment_start_datetime_utc=data["start"],
            appointment_end_datetime_utc=data["end"],
            location=data["assignment"],
            reason="Check-up",
        )
        assert str(appt) == f"Appointment: {data['patient']} with {data['provider']} at {data['start']}"
        assert appt.status == Appointment.Status.REQUESTED

    def test_past_start_blocked(self, data):
        with pytest.raises(ValidationError, match="past start time"):
            Appointment(
                patient=data["patient"],
                healthcare_provider=data["provider"],
                appointment_start_datetime_utc=timezone.now() - timedelta(minutes=1),
                appointment_end_datetime_utc=timezone.now() + timedelta(hours=1),
                location=data["assignment"],
                reason="x",
            ).clean()

    def test_end_before_start_blocked(self, data):
        with pytest.raises(IntegrityError, match="end_datetime_utc_gt_start_datetime"):
            Appointment.objects.create(
                patient=data["patient"],
                healthcare_provider=data["provider"],
                appointment_start_datetime_utc=data["start"],
                appointment_end_datetime_utc=data["start"] - timedelta(minutes=1),
                location=data["assignment"],
                reason="x",
            )

class TestSlotModel:
    @pytest.fixture
    def slot_data(self, hospital_factory, provider_factory):
        h = hospital_factory()
        provider = provider_factory()
        now = timezone.now()
        return {
            "healthcare_provider": provider,
            "hospital": h,
            "start": now + timedelta(hours=1),
            "end": now + timedelta(hours=2),
        }

    def test_slot_duration(self, slot_data):
        slot = Slot.objects.create(**slot_data)
        assert slot.duration == timedelta(hours=1)

    def test_is_past(self, slot_data):
        slot = Slot(
            healthcare_provider=slot_data["healthcare_provider"],
            hospital=slot_data["hospital"],
            start=timezone.now() - timedelta(hours=2),
            end=timezone.now() - timedelta(hours=1),
        )
        assert slot.is_past() is True
        assert slot.is_booked() is False

    def test_unique_provider_start(self, slot_data):
        Slot.objects.create(**slot_data)
        with pytest.raises(IntegrityError):
            Slot.objects.create(**slot_data)

    def test_free_slot_unique(self, slot_data):
        Slot.objects.create(**slot_data, status=Slot.Status.FREE)
        # second FREE slot same start → violates partial unique constraint
        with pytest.raises(IntegrityError):
            Slot.objects.create(**slot_data, status=Slot.Status.FREE)

    def test_past_slot_blocked(self, slot_data):
        with pytest.raises(ValidationError, match="past"):
            Slot(
                healthcare_provider=slot_data["healthcare_provider"],
                hospital=slot_data["hospital"],
                start=timezone.now() - timedelta(hours=2),
                end=timezone.now() - timedelta(hours=1),
            ).clean()