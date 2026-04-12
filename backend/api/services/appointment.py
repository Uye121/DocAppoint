from datetime import time, timedelta
from django.utils import timezone
from zoneinfo import ZoneInfo

from ..models import Slot
from ..metrics import slots_generated_total


def generate_daily_slots(
    provider, hospital, date, duration_min=30, opening=time(9), closing=time(17)
):
    """
    Generate appointment slots for provider

    Args:
        provider (HealthcareProvider): the healthcare provider to generate appointment slots for
        hospital (Hospital): the hospital the healthcare provider is in
        date (timezone.datetime): the date of the slot
        duration (int): the duration of the appointment slot in minutes (default is 30)
        opening (time): the opening time of the slots for the day
        closing (time): the closing time of the slots for the day
    """
    tz = ZoneInfo(hospital.timezone)
    start_dt = timezone.make_aware(timezone.datetime.combine(date, opening), tz)
    end_dt = timezone.make_aware(timezone.datetime.combine(date, closing), tz)

    slot_start = start_dt
    slots = []
    while slot_start + timedelta(minutes=duration_min) <= end_dt:
        slot_end = slot_start + timedelta(minutes=duration_min)
        slots.append(
            Slot(
                healthcare_provider=provider,
                hospital=hospital,
                start=slot_start,
                end=slot_end,
                status=Slot.Status.FREE,
            )
        )
        slot_start = slot_end

    slots_created = Slot.objects.bulk_create(slots, ignore_conflicts=True)
    slots_generated_total.labels(
        hospital_id=str(hospital.id), status=Slot.Status.FREE
    ).inc(len(slots_created))
