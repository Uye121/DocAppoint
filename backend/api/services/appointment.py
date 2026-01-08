from django.db.models import Q
from datetime import time, timedelta
from django.utils import timezone
from zoneinfo import ZoneInfo

from ..models import Slot, Appointment

def refresh_slot_status(provider, hospital, start, end):
    """
    Mark slots BOOKED when they overlap a CONFIRMED appointment.
    """
    overlap_q = Q(
        healthcare_provider=provider,
        hospital=hospital,
        start__lt=end,
        end__gt=start, 
        status=Slot.Status.FREE,
    )

    # all appointments that collide
    apps = Appointment.objects.filter(
        healthcare_provider=provider,
        location__hospital=hospital,
        status=Appointment.Status.CONFIRMED,
        appointment_start_datetime_utc__lt=end,
        appointment_end_datetime_utc__gt=start,
    )

    if apps.exists():
        Slot.objects.filter(overlap_q).update(status=Slot.Status.BOOKED)

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
