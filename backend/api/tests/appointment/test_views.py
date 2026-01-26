import pytest
from datetime import timedelta, time
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from ...models import (
    Appointment,
    Slot,
    ProviderHospitalAssignment,
)
from ...services.appointment import generate_daily_slots

User = get_user_model()
pytestmark = pytest.mark.django_db(transaction=True)


class TestAppointmentViewSet:
    url = "/api/appointment/"

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def data(
        self, hospital_factory, provider_factory, patient_factory, admin_staff_factory
    ):
        a = admin_staff_factory()
        h = hospital_factory()
        provider = provider_factory()
        patient = patient_factory()
        assignment = ProviderHospitalAssignment.objects.create(
            healthcare_provider=provider,
            hospital=h,
            created_by=a.user,
            updated_by=a.user,
        )
        now = timezone.now().replace(second=0, microsecond=0)
        today = (timezone.now() + timedelta(days=1)).date()
        open_time = time(9, 0)
        close_time = time(17, 0)
        anchor = now + timedelta(hours=1)

        generate_daily_slots(
            provider=provider,
            hospital=h,
            opening=open_time,
            closing=close_time,
            date=today,
        )

        return {
            "patient": patient,
            "provider": provider,
            "assignment": assignment,
            "hospital": h,
            "anchor": anchor,
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
            location=data["hospital"],
            reason="Mine",
        )
        res = api_client.get(self.url)
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 1

    def test_provider_sees_own_appointments(self, api_client, data):
        api_client.force_authenticate(user=data["provider"].user)
        Appointment.objects.create(
            patient=data["patient"],
            healthcare_provider=data["provider"],
            appointment_start_datetime_utc=data["start"],
            appointment_end_datetime_utc=data["end"],
            location=data["hospital"],
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

        free_slot = Slot.objects.filter(
            healthcare_provider=data["provider"],
            hospital=data["hospital"],
            status=Slot.Status.FREE,
        ).first()

        payload = {
            "patient": data["patient"].pk,
            "provider": data["provider"].pk,
            "appointment_start_datetime_utc": free_slot.start.isoformat(),
            "appointment_end_datetime_utc": free_slot.end.isoformat(),
            "location": data["hospital"].pk,
            "reason": "Check-up",
        }
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        assert Appointment.objects.count() == 1
        appt = Appointment.objects.first()
        assert appt.patient == data["patient"]

    def test_provider_can_book_for_patient(self, api_client, data):
        api_client.force_authenticate(user=data["provider"].user)

        free_slot = Slot.objects.filter(
            healthcare_provider=data["provider"],
            hospital=data["hospital"],
            status=Slot.Status.FREE,
        ).first()

        payload = {
            "patient": data["patient"].pk,
            "provider": data["provider"].pk,
            "appointment_start_datetime_utc": free_slot.start.isoformat(),
            "appointment_end_datetime_utc": free_slot.end.isoformat(),
            "location": data["hospital"].pk,
            "reason": "Check-up",
        }
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        appt = Appointment.objects.first()
        assert appt.patient == data["patient"]

    def test_provider_book_patient_required(self, api_client, data):
        api_client.force_authenticate(user=data["provider"].user)
        start = data["anchor"] + timedelta(hours=1)
        payload = {
            "provider": data["provider"].pk,
            "appointment_start_datetime_utc": start.isoformat(),
            "appointment_end_datetime_utc": start + timedelta(minutes=30),
            "location": data["hospital"].pk,
            "reason": "No patient",
        }
        res = api_client.post(self.url, payload, format="json")
        print(res.data)
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "Required when booking appointment for patient" in res.data["patient"]

    def test_past_start_blocked(self, api_client, data):
        api_client.force_authenticate(user=data["patient"].user)
        past = timezone.now() - timedelta(minutes=5)
        payload = {
            "healthcare_provider": data["provider"].pk,
            "appointment_start_datetime_utc": past.isoformat(),
            "appointment_end_datetime_utc": past + timedelta(minutes=30),
            "location": data["hospital"].pk,
            "reason": "Past",
        }
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            "Cannot schedule an appointment in the past."
            in res.data["appointment_start_datetime_utc"][0]
        )


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
            healthcare_provider=provider,
            hospital=provider.primary_hospital,
            start=timezone.make_aware(
                timezone.datetime.combine(tomorrow, timezone.datetime.min.time())
            )
            + timedelta(hours=9),
            end=timezone.make_aware(
                timezone.datetime.combine(tomorrow, timezone.datetime.min.time())
            )
            + timedelta(hours=10),
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
            "healthcare_provider": provider.pk,
            "hospital_id": provider.primary_hospital.pk,
            "start": timezone.make_aware(
                timezone.datetime.combine(tomorrow, timezone.datetime.min.time())
                + timedelta(hours=9)
            ).isoformat(),
            "end": timezone.make_aware(
                timezone.datetime.combine(tomorrow, timezone.datetime.min.time())
                + timedelta(hours=10)
            ).isoformat(),
            "status": "FREE",
        }
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        assert Slot.objects.count() == 1
        slot = Slot.objects.first()
        assert slot.healthcare_provider == provider

    def test_free_slots_action(self, api_client, provider):
        api_client.force_authenticate(user=provider.user)
        tomorrow = timezone.now().date() + timedelta(days=1)
        Slot.objects.create(
            healthcare_provider=provider,
            hospital=provider.primary_hospital,
            start=timezone.make_aware(
                timezone.datetime.combine(tomorrow, timezone.datetime.min.time())
            )
            + timedelta(hours=9),
            end=timezone.make_aware(
                timezone.datetime.combine(tomorrow, timezone.datetime.min.time())
            )
            + timedelta(hours=10),
            status=Slot.Status.FREE,
        )
        Slot.objects.create(
            healthcare_provider=provider,
            hospital=provider.primary_hospital,
            start=timezone.make_aware(
                timezone.datetime.combine(tomorrow, timezone.datetime.min.time())
            )
            + timedelta(hours=10),
            end=timezone.make_aware(
                timezone.datetime.combine(tomorrow, timezone.datetime.min.time())
            )
            + timedelta(hours=11),
            status=Slot.Status.BOOKED,
        )
        res = api_client.get(
            self.url + "free/", {"date": tomorrow.isoformat(), "provider": provider.pk}
        )
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 1


class TestAppointmentSetStatus:
    url = "/api/appointment/"

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def data(
        self, provider_factory, hospital_factory, patient_factory, admin_staff_factory
    ):
        a = admin_staff_factory()
        h = hospital_factory()
        provider = provider_factory()
        patient = patient_factory()
        ProviderHospitalAssignment.objects.create(
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
            "start": now + timedelta(hours=1),
            "end": now + timedelta(hours=2),
        }

    def test_confirm_changes_status_and_blocks_slots(self, api_client, data):
        slot = Slot.objects.create(
            healthcare_provider=data["provider"],
            hospital=data["hospital"],
            start=data["start"],
            end=data["end"],
            status=Slot.Status.FREE,
        )
        appt = Appointment.objects.create(
            patient=data["patient"],
            healthcare_provider=data["provider"],
            appointment_start_datetime_utc=data["start"],
            appointment_end_datetime_utc=data["end"],
            location=data["hospital"],
            reason="Check-up",
            status=Appointment.Status.REQUESTED,
        )

        api_client.force_authenticate(user=data["patient"].user)
        res = api_client.post(
            f"{self.url}{appt.pk}/set-status/", {"status": "CONFIRMED"}
        )
        assert res.status_code == status.HTTP_200_OK
        assert res.data["detail"] == "Appointment confirmed."

        appt.refresh_from_db()
        assert appt.status == Appointment.Status.CONFIRMED

        slot.refresh_from_db()
        assert slot.status == Slot.Status.BOOKED

    def test_reject_requested_appointment(self, api_client, data):
        appt = Appointment.objects.create(
            patient=data["patient"],
            healthcare_provider=data["provider"],
            appointment_start_datetime_utc=data["start"],
            appointment_end_datetime_utc=data["end"],
            location=data["hospital"],
            reason="Reject me",
            status=Appointment.Status.REQUESTED,
        )

        api_client.force_authenticate(user=data["patient"].user)
        res = api_client.post(
            f"{self.url}{appt.pk}/set-status/", {"status": "CANCELLED"}
        )
        assert res.status_code == status.HTTP_200_OK
        assert res.data["detail"] == "Appointment cancelled."

        appt.refresh_from_db()
        assert appt.status == Appointment.Status.CANCELLED

    def test_cannot_confirm_non_requested(self, api_client, data):
        appt = Appointment.objects.create(
            patient=data["patient"],
            healthcare_provider=data["provider"],
            appointment_start_datetime_utc=data["start"],
            appointment_end_datetime_utc=data["end"],
            location=data["hospital"],
            reason="Already confirmed",
            status=Appointment.Status.CONFIRMED,
        )
        api_client.force_authenticate(user=data["patient"].user)
        res = api_client.post(
            f"{self.url}{appt.pk}/set-status/", {"status": "CONFIRMED"}
        )
        print(res.data)
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "Prohibited status change" in res.data["detail"]

    def test_invalid_transition_returns_400(self, api_client, data):
        appt = Appointment.objects.create(
            patient=data["patient"],
            healthcare_provider=data["provider"],
            appointment_start_datetime_utc=data["start"],
            appointment_end_datetime_utc=data["end"],
            location=data["hospital"],
            reason="Bad transition",
            status=Appointment.Status.CONFIRMED,
        )
        api_client.force_authenticate(user=data["patient"].user)
        res = api_client.post(
            f"{self.url}{appt.pk}/set-status/", {"status": "REQUESTED"}
        )
        print(res.data)
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "Prohibited status change" in res.data["detail"]


class TestGenerateSlots:
    url = "/api/appointment/generate-slots/"

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def provider(self, provider_factory):
        return provider_factory()

    def test_provider_can_generate_own_slots(self, api_client, provider):
        api_client.force_authenticate(user=provider.user)
        tomorrow = (timezone.now() + timedelta(days=1)).date()

        payload = {
            "provider": str(provider.pk),
            "date": tomorrow.isoformat(),
            "duration": 20,
            "opening": "08:30",
            "closing": "12:00",
        }
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data["detail"] == "Slots generated."

        slots = Slot.objects.filter(healthcare_provider=provider, start__date=tomorrow)
        assert slots.count() == 10  # 08:30-12:00 with 20-min steps

        first = slots.first()
        assert first.start.time() == time(8, 30)
        assert first.end.time() == time(8, 50)

    def test_missing_provider_or_date_400(self, api_client, provider):
        api_client.force_authenticate(user=provider.user)
        res = api_client.post(self.url, {}, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "Provider and date are required." in res.data["detail"]

    def test_invalid_time_format_400(self, api_client, provider):
        api_client.force_authenticate(user=provider.user)
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        payload = {
            "provider": str(provider.pk),
            "date": tomorrow.isoformat(),
            "opening": "25:00",
            "closing": "17:00",
        }
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "opening / closing must be HH:MM (24-hour)." in res.data["detail"]

    def test_closing_not_after_opening_400(self, api_client, provider):
        api_client.force_authenticate(user=provider.user)
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        payload = {
            "provider": str(provider.pk),
            "date": tomorrow.isoformat(),
            "opening": "14:00",
            "closing": "14:00",
        }
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "closing must be after opening." in res.data["detail"]


class TestSlotRange:
    url = "/api/slot/range/"

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def provider(self, provider_factory):
        return provider_factory()

    def test_range_default_week(self, api_client, provider):
        today = timezone.now().date()
        monday = today - timedelta(days=today.weekday())
        # sunday = monday + timedelta(days=6)

        for i in range(7):
            day = monday + timedelta(days=i)
            Slot.objects.create(
                healthcare_provider=provider,
                hospital=provider.primary_hospital,
                start=timezone.make_aware(
                    timezone.datetime.combine(day, timezone.datetime.min.time())
                    + timedelta(hours=9)
                ),
                end=timezone.make_aware(
                    timezone.datetime.combine(day, timezone.datetime.min.time())
                    + timedelta(hours=9, minutes=30)
                ),
                status=Slot.Status.FREE,
            )

        api_client.force_authenticate(user=provider.user)
        res = api_client.get(f"{self.url}?provider={provider.pk}")
        assert res.status_code == status.HTTP_200_OK

        grouped = res.data
        # expected_days = (sunday - today).days + 1
        assert len(grouped) == 7
        for _, slots in grouped.items():
            assert len(slots) == 1
            print(slots)
            assert slots[0]["hospitalId"] == provider.primary_hospital.pk

    def test_range_custom_dates(self, api_client, provider):
        start_date = timezone.now().date() + timedelta(days=3)
        end_date = start_date + timedelta(days=2)  # 3-day span

        # slots outside range
        Slot.objects.create(
            healthcare_provider=provider,
            hospital=provider.primary_hospital,
            start=timezone.make_aware(
                timezone.datetime.combine(start_date - timedelta(days=1), time(10))
            ),
            end=timezone.make_aware(
                timezone.datetime.combine(start_date - timedelta(days=1), time(10, 30))
            ),
            status=Slot.Status.FREE,
        )
        # slots inside range
        for i in range(3):
            day = start_date + timedelta(days=i)
            Slot.objects.create(
                healthcare_provider=provider,
                hospital=provider.primary_hospital,
                start=timezone.make_aware(timezone.datetime.combine(day, time(9))),
                end=timezone.make_aware(timezone.datetime.combine(day, time(9, 30))),
                status=Slot.Status.FREE,
            )

        api_client.force_authenticate(user=provider.user)
        res = api_client.get(
            f"{self.url}?provider={provider.pk}"
            f"&start_date={start_date.isoformat()}&end_date={end_date.isoformat()}"
        )
        assert res.status_code == status.HTTP_200_OK

        grouped = res.data
        assert len(grouped) == 3
        for day_str in grouped:
            day = timezone.datetime.fromisoformat(day_str).date()
            assert start_date <= day <= end_date

    def test_invalid_date_format_400(self, api_client, provider):
        api_client.force_authenticate(user=provider.user)
        res = api_client.get(
            f"{self.url}?provider={provider.pk}&start_date=bad&end_date=2026-02-30"
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "Dates must be YYYY-MM-DD." in res.data["detail"]

    def test_end_before_start_400(self, api_client, provider):
        api_client.force_authenticate(user=provider.user)
        today = timezone.now().date()
        res = api_client.get(
            f"{self.url}?provider={provider.pk}"
            f"&start_date={today}&end_date={today - timedelta(days=1)}"
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "end_date must be >= start_date." in res.data["detail"]
