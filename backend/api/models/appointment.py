from datetime import timedelta
from zoneinfo import ZoneInfo
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from ..mixin import TimestampMixin, AuditMixin
from .users import Patient, HealthcareProvider
from .hospital import Hospital, ProviderHospitalAssignment

class Appointment(TimestampMixin):
    class Status(models.TextChoices):
        REQUESTED = "REQUESTED", "Requested"
        CONFIRMED = "CONFIRMED", "Confirmed"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        RESCHEDULED = "RESCHEDULED", "Rescheduled"
        
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="patient_appointments")
    healthcare_provider = models.ForeignKey(HealthcareProvider, on_delete=models.CASCADE, related_name="provider_appointments")
    appointment_start_datetime_utc= models.DateTimeField()
    appointment_end_datetime_utc= models.DateTimeField()
    location = models.ForeignKey(ProviderHospitalAssignment, on_delete=models.PROTECT, related_name='appointments')
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    
    class Meta(TimestampMixin.Meta):
        unique_together = ('patient', 'healthcare_provider', 'appointment_start_datetime_utc')
        constraints = [
            models.CheckConstraint(
                name='appointment_end_datetime_utc_gt_start_datetime',
                condition=models.Q(appointment_end_datetime_utc__gt=models.F('appointment_start_datetime_utc'))
            )
        ]
    
    def clean(self):
        super().clean()
        
        if self.appointment_start_datetime_utc and self.appointment_start_datetime_utc < timezone.now():
            raise ValidationError({'message': 'Cannot schedule an appointment with a past start time.'})

        if self.appointment_end_datetime_utc and self.appointment_end_datetime_utc < timezone.now():
            raise ValidationError({'message': 'Cannot schedule an appointment with a past end time.'})
    
    def __str__(self):
        return f"Appointment: {self.patient} with {self.healthcare_provider} at {self.appointment_start_datetime_utc}"
    
class Slot(TimestampMixin, AuditMixin):
    class Status(models.TextChoices):
        FREE = "FREE", "Free"
        BOOKED = "BOOKED", "Booked"
        BLOCKED = "BLOCKED", "Blocked" 
        UNAVAILABLE = "UNAVAILABLE", "Unavailable"

    healthcare_provider = models.ForeignKey(HealthcareProvider,on_delete=models.CASCADE, related_name="slots")
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='slots')
    start = models.DateTimeField()
    end = models.DateTimeField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.FREE) 
    created_by = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='slots_created')
    updated_by = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='slots_updated')
    
    class Meta(TimestampMixin.Meta, AuditMixin.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["healthcare_provider", "start"],
                name="uniq_healthcare_provider_start"
            ),
            models.CheckConstraint(
                condition=models.Q(end__gt=models.F("start")),
                name="slot_end_gt_start"
            ),
            models.UniqueConstraint(
                fields=["healthcare_provider", "start"],
                condition=models.Q(status="FREE"),
                name="uniq_healthcare_provider_start_free"
            )
        ]
        indexes = [
            models.Index(fields=["healthcare_provider", "start", "status"]),
            models.Index(fields=["hospital", "start", "status"]),
        ]

    @property
    def duration(self) -> timedelta:
        return self.end - self.start
    
    def is_past(self) -> bool:
        return self.end < timezone.now()
    
    def is_booked(self) -> bool:
        return self.status == self.Status.BOOKED
    
    def clean(self):
        super().clean()

        if self.start >= self.end:
            raise ValidationError("End time must be after start time.")

        if self.is_past():
            raise ValidationError("Cannot create/modify a slot in the past.")
        
    def __str__(self):
        tz = ZoneInfo(self.hospital.timezone)
        start_local = self.start.astimezone(tz)
        end_local = self.end.astimezone(tz)
        return (
            f"{self.healthcare_provider} @ {self.hospital}  "
            f"{start_local:%Y-%m-%d %H:%M}–{end_local:%H:%M} ({self.status})"
        )
