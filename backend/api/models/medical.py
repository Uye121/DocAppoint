from django.db import models
from django.utils.translation import gettext_lazy as _

from ..mixin import TimestampMixin, AuditMixin
from .users import Patient, HealthcareProvider

class MedicalRecord(TimestampMixin, AuditMixin):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="medical_records")
    healthcare_provider = models.ForeignKey(HealthcareProvider, on_delete=models.CASCADE)
    diagnosis = models.TextField()
    notes = models.TextField()
    prescriptions = models.TextField()

    # Attributes for soft-delete
    is_removed = models.BooleanField(default=False, db_index=True)
    removed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta(TimestampMixin.Meta, AuditMixin.Meta):
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Medical Record: {self.patient} - {self.updated_at}"