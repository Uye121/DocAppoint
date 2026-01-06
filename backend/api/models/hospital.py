from zoneinfo import available_timezones
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ..mixin import AuditMixin

class Hospital(AuditMixin, models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    phone_number = models.CharField(max_length=20)
    timezone = models.CharField(
        max_length=64,
        choices=[(z, z) for z in sorted(available_timezones())],
        default='UTC'
    )

    # Attributes for soft-delete
    is_removed = models.BooleanField(default=False, db_index=True)
    removed_at = models.DateTimeField(null=True, blank=True)

class ProviderHospitalAssignment(models.Model):
    provider = models.ForeignKey('HealthcareProvider', on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    start_datetime_utc = models.DateTimeField(default=timezone.now)
    end_datetime_utc = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['provider', 'hospital']
        indexes = [
            models.Index(fields=["provider", "is_active"]),
        ]
        # Provider can only be assigned to same hospital only after previous
        # assignment has ended
        constraints = [
            models.UniqueConstraint(
                fields=['provider', 'hospital'],
                condition=models.Q(end_datetime_utc__isnull=True),
                name="unique_provider_hospital_assignment"
            )
        ]
