from django.db import models
from django.utils.translation import gettext_lazy as _
from .users import User

from ..mixin import AuditMixin
from .speciality import Speciality
from .hospital import Hospital

class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="patient_profile")
    blood_type = models.CharField(_("Blood Type"), max_length=5, blank=True)
    allergies = models.TextField(_("Allergies"), blank=True)
    chronic_conditions = models.TextField(_("Chronic Conditions"), blank=True)
    current_medications = models.TextField(_("Current Medications"), blank=True)
    insurance = models.CharField(_("Insurance"), max_length=255, blank=True)
    weight = models.PositiveIntegerField(_("Weight (kg)"), blank=True, null=True, help_text="Weight in kg")
    height = models.PositiveIntegerField(_("Height (cm)"), blank=True, null=True, help_text="Height in centimeters")
    
    def __str__(self):
        return f"Patient Profile: {self.user.username}"
    
class HealthcareProviderProfile(AuditMixin, models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="healthcare_provider_profile")
    speciality = models.ForeignKey(Speciality, on_delete=models.CASCADE, related_name='provider_speciality')
    image = models.ImageField(upload_to='healthcare_providers')
    education = models.TextField(_("Education"), blank=True)
    years_of_experience = models.PositiveIntegerField(_("Years of Experience"), default=0)
    about = models.TextField()
    fees = models.DecimalField(max_digits=9, decimal_places=2)
    address_line1 = models.CharField("Address line 1", max_length=1024)
    address_line2 = models.CharField("Address line 2", max_length=1024, blank=True)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=2)
    zip_code = models.CharField(max_length=5)
    license_number = models.CharField(_("License Number"), max_length=100)
    certifications = models.TextField(_("Certifications"), blank=True)
    
    # Affiliations
    hospitals = models.ManyToManyField(Hospital, through="ProviderHospitalAssignment")
    primary_hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, null=True, blank=True, related_name="primary_provider")

    # Attributes for soft-delete
    is_removed = models.BooleanField(default=False, db_index=True)
    removed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta(AuditMixin.Meta):
        constraints = [
            models.CheckConstraint(
                name="experience_non_negative",
                check=models.Q(years_of_experience__gte=0)
            ),
            models.CheckConstraint(
                name="fees_above_0",
                check=models.Q(fees__gt=0)
            ),
            models.CheckConstraint(
                name="valid_license_format",
                check=models.Q(license_number__regex=r'^[A-Z0-9]{6,20}$')
            )
        ]
        
    def __str__(self):
        return f"Healthcare Provider Profile: {self.user.username} - {self.speciality.name}"
    
class AdminStaffProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="admin_staff_profile")
    
    # Affiliation
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='admin_staff')
    
    def __str__(self):
        return f"Admin Staff: {self.user.username} - {self.hospital.name}"
    
class SystemAdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="system_admin_profile")
    
    def __str__(self):
        return f"System Admin Staff: {self.user.username}"
