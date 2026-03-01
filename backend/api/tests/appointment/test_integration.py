import pytest
from datetime import timedelta, datetime, time
from django.utils import timezone
from django.urls import reverse
from rest_framework import status

from api.models import Appointment, Slot


pytestmark = pytest.mark.django_db


class TestAppointmentWorkflow:
    def test_patient_books_appointment_flow(
        self, authenticated_patient_client, authenticated_provider_client
    ):
        """Test complete flow: provider creates slots -> patient books -> provider confirms"""
        provider_client, provider = authenticated_provider_client()
        patient_client, patient = authenticated_patient_client()
        hospital = provider.primary_hospital

        slot_url = reverse("slot-list")
        slot_times = []

        base_date = timezone.now().date() + timedelta(days=3)
        for hour in [9, 10, 11]:
            start = timezone.make_aware(datetime.combine(base_date, time(hour, 0)))
            end = start + timedelta(minutes=30)
            slot_times.append((start, end))

            slot_data = {
                "healthcare_provider": provider.pk,
                "hospital_id": hospital.id,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "status": Slot.Status.FREE,
            }
            response = provider_client.post(slot_url, slot_data, format="json")
            assert response.status_code == status.HTTP_201_CREATED

        assert Slot.objects.filter(healthcare_provider=provider).count() == 3

        free_slots_url = reverse("slot-free")
        params = {"provider": provider.pk, "date": base_date.isoformat()}
        response = patient_client.get(free_slots_url, params)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

        appointment_url = reverse("appointment-list")
        chosen_start, chosen_end = slot_times[1]

        appointment_data = {
            "provider": provider.pk,
            "patient": patient.pk,
            "location": hospital.id,
            "appointment_start_datetime_utc": chosen_start.isoformat(),
            "appointment_end_datetime_utc": chosen_end.isoformat(),
            "reason": "Annual checkup",
        }

        response = patient_client.post(appointment_url, appointment_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        appointment_id = response.data["id"]

        # Verify slot is now booked
        slot = Slot.objects.get(healthcare_provider=provider, start=chosen_start)
        assert slot.status == Slot.Status.BOOKED

        confirm_url = reverse("appointment-set-status", args=[appointment_id])
        confirm_data = {"status": Appointment.Status.CONFIRMED}

        response = provider_client.post(confirm_url, confirm_data, format="json")
        assert response.status_code == status.HTTP_200_OK

        appointment = Appointment.objects.get(id=appointment_id)
        assert appointment.status == Appointment.Status.CONFIRMED

    def test_appointment_rescheduling_flow(
        self,
        authenticated_patient_client,
        authenticated_provider_client,
        appointment_factory,
        slot_factory,
    ):
        """Test complete rescheduling flow"""
        provider_client, provider = authenticated_provider_client()
        _, patient = authenticated_patient_client()
        hospital = provider.primary_hospital

        base_date = timezone.now().date() + timedelta(days=5)
        original_start = timezone.make_aware(datetime.combine(base_date, time(10, 0)))
        original_end = original_start + timedelta(hours=1)

        appointment = appointment_factory(
            patient=patient,
            healthcare_provider=provider,
            location=hospital,
            appointment_start_datetime_utc=original_start,
            appointment_end_datetime_utc=original_end,
            status=Appointment.Status.CONFIRMED,
        )

        # Create booked slot for original time
        slot_factory(
            healthcare_provider=provider,
            hospital=hospital,
            start=original_start,
            end=original_end,
            status=Slot.Status.BOOKED,
            appointment=appointment,
            created_by=provider.user,
            updated_by=provider.user,
        )

        # Create new available slot for rescheduling
        new_date = base_date + timedelta(days=2)
        new_start = timezone.make_aware(datetime.combine(new_date, time(10, 0)))
        new_end = new_start + timedelta(hours=1)
        new_slot = slot_factory(
            healthcare_provider=provider,
            hospital=hospital,
            start=new_start,
            end=new_end,
            status=Slot.Status.FREE,
            appointment=None,
            created_by=provider.user,
            updated_by=provider.user,
        )

        # Patient requests reschedule (through provider)
        reschedule_url = reverse("appointment-set-status", args=[appointment.id])
        reschedule_data = {
            "status": Appointment.Status.RESCHEDULED,
            "new_start_datetime_utc": new_start.isoformat(),
            "new_end_datetime_utc": new_end.isoformat(),
        }

        response = provider_client.post(reschedule_url, reschedule_data, format="json")
        assert response.status_code == status.HTTP_200_OK

        # Verify appointment was rescheduled
        appointment.refresh_from_db()
        assert appointment.status == Appointment.Status.RESCHEDULED
        assert appointment.appointment_start_datetime_utc == new_start
        assert appointment.appointment_end_datetime_utc == new_end

        # Verify old slot is now free
        old_slot = Slot.objects.get(healthcare_provider=provider, start=original_start)
        assert old_slot.status == Slot.Status.FREE
        assert old_slot.appointment is None

        # Verify new slot is booked
        new_slot = Slot.objects.get(healthcare_provider=provider, start=new_start)
        assert new_slot.status == Slot.Status.BOOKED
        assert new_slot.appointment == appointment

    def test_appointment_cancellation_flow(
        self,
        authenticated_patient_client,
        authenticated_provider_client,
        appointment_factory,
        slot_factory,
    ):
        """Test complete cancellation flow"""
        patient_client, patient = authenticated_patient_client()
        provider_client, provider = authenticated_provider_client()

        hospital = provider.primary_hospital

        # Create datetime for future appointment
        base_date = timezone.now().date() + timedelta(days=3)
        start_time = timezone.make_aware(datetime.combine(base_date, time(14, 0)))
        end_time = start_time + timedelta(minutes=30)

        # Create confirmed appointment
        appointment = appointment_factory(
            patient=patient,
            healthcare_provider=provider,
            location=hospital,
            appointment_start_datetime_utc=start_time,
            appointment_end_datetime_utc=end_time,
            status=Appointment.Status.CONFIRMED,
        )

        # Create booked slot linked to appointment
        slot = slot_factory(
            healthcare_provider=provider,
            hospital=hospital,
            start=start_time,
            end=end_time,
            status=Slot.Status.BOOKED,
            appointment=appointment,
            created_by=provider.user,
            updated_by=provider.user,
        )

        assert appointment.status == Appointment.Status.CONFIRMED
        assert slot.status == Slot.Status.BOOKED
        assert slot.appointment == appointment

        # Patient cancels appointment
        cancel_url = reverse("appointment-set-status", args=[appointment.id])
        cancel_data = {"status": Appointment.Status.CANCELLED}

        response = patient_client.post(cancel_url, cancel_data, format="json")
        assert response.status_code == status.HTTP_200_OK

        # Refresh objects from DB
        appointment.refresh_from_db()
        slot.refresh_from_db()

        # Verify appointment is cancelled
        assert appointment.status == Appointment.Status.CANCELLED

        # Verify slot is now free and unlinked from appointment
        assert slot.status == Slot.Status.FREE
        assert slot.appointment is None

        provider_response = provider_client.get(
            reverse("appointment-list"), {"status": Appointment.Status.CANCELLED}
        )
        assert provider_response.status_code == status.HTTP_200_OK

        cancelled_appointments = [
            appt for appt in provider_response.data if appt["id"] == appointment.id
        ]
        assert len(cancelled_appointments) == 1
