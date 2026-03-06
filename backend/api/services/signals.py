from django.db.models.signals import post_save
from django.dispatch import receiver
from ..models import MedicalRecord, Appointment

@receiver(post_save, sender=MedicalRecord)
def update_appointment_status(sender, instance, created, **kwargs):
    """Update appointment status to COMPLETED when a medical record is created"""
    if created:  # Only on creation
        try:
            appointment = instance.appointment
            appointment.status = 'COMPLETED'
            appointment.save()
        except Appointment.DoesNotExist:
            pass