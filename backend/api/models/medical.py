from django.db import models
from django.core.exceptions import ValidationError

from ..mixin import TimestampMixin, AuditMixin
from .users import Patient, HealthcareProvider, Hospital
from ..models import Appointment


class MedicalRecord(TimestampMixin, AuditMixin):
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="medical_records"
    )
    healthcare_provider = models.ForeignKey(
        HealthcareProvider, on_delete=models.CASCADE
    )
    hospital = models.ForeignKey(
        Hospital, on_delete=models.CASCADE,
    )
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name="medical_record",
    )
    diagnosis = models.TextField()
    notes = models.TextField()
    prescriptions = models.TextField()

    # Attributes for soft-delete
    is_removed = models.BooleanField(default=False, db_index=True)
    removed_at = models.DateTimeField(null=True, blank=True)

    class Meta(TimestampMixin.Meta, AuditMixin.Meta):
        ordering = ["-created_at"]

    def clean(self):
        if not self.diagnosis:
            raise ValidationError({"diagnosis": "Diagnosis is required"})
        if not self.notes:
            raise ValidationError({"notes": "Notes is required"})
        
    def save(self, *args, **kwargs):
        self.full_clean() 
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Medical Record: {self.patient} - {self.updated_at}"
