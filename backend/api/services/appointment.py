from datetime import time, timedelta
from django.utils import timezone
from zoneinfo import ZoneInfo

from ..models import Slot

def generate_daily_slots(
    provider,
    hospital,
    date,
    duration_min=30,
    opening=time(9),
    closing=time(17)
):
    tz = ZoneInfo(hospital.timezone)
    start_dt = timezone.make_aware(timezone.datetime.combine(date, opening), tz)
    end_dt   = timezone.make_aware(timezone.datetime.combine(date, closing), tz)

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

    Slot.objects.bulk_create(slots, ignore_conflicts=True)
