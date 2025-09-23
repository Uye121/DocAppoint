from typing import List, Dict, Optional, Union
from datetime import datetime, timedelta
from django.db import models
from django.utils import timezone
from django.db.models.query import QuerySet
from django.contrib.auth.models import AbstractUser, Group
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class BaseModel(models.Model):
    created_at = models.DateTimeField(db_index=True, default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        
class Speciality(models.Model):
    name = models.CharField(max_length=180, unique=True)
    image = models.FileField(upload_to='speciality')
    
    def __str__(self):
        return self.name
    
class Hospital(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    phone_number = models.CharField(max_length=20)

class User(BaseModel, AbstractUser):
    class UserType(models.TextChoices):
        PATIENT = "PATIENT", "Patient"
        HEALTHCARE_PROVIDER = "HEALTHCARE_PROVIDER", "Healthcare Provider"
        ADMIN_STAFF = "ADMIN_STAFF", "Admin Staff"
        SYSTEM_ADMIN = "SYSTEM_ADMIN", "System Admin"
        
    base_type = UserType.PATIENT
    
    type = models.CharField(
        _("Type"), max_length=50, choices=UserType.choices, default=base_type
    )
    
    date_of_birth = models.DateField(_("Date of Birth"), null=True, blank=True)
    phone_number = models.CharField(_("Phone Number"), max_length=20, blank=True)
    address = models.TextField(_("Address"), blank=True)
            
    def clean(self):
        super().clean()
        
        if not self.password:
            raise ValidationError("Password is required")
        
        if not self.password.strip():
            raise ValidationError("Password cannot be empty")
        
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.username}: {self.get_type_display()}" # type: ignore
    
class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="patient_profile")
    age = models.PositiveIntegerField(_("Age"), blank=True)
    blood_type = models.CharField(_("Blood Type"), max_length=5, blank=True)
    allergies = models.TextField(_("Allergies"), blank=True)
    chronic_conditions = models.TextField(_("Chronic Conditions"), blank=True)
    current_medications = models.TextField(_("Current Medications"), blank=True)
    insurance = models.CharField(_("Insurance"), max_length=255, blank=True)
    weight = models.PositiveIntegerField(_("Weight (kg)"), blank=True, null=True, help_text="Weight in grams")
    height = models.PositiveIntegerField(_("Height (cm)"), blank=True, null=True, help_text="Height in centimeters")
    
    def __str__(self):
        return f"Patient Profile: {self.user.username}"
    
class HealthcareProviderProfile(models.Model):
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
    
    class Meta:
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
    
class ProviderHospitalAssignment(models.Model):
    provider = models.ForeignKey(HealthcareProviderProfile, on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    start_datetime_utc = models.DateTimeField(default=timezone.now)
    end_datetime_utc = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['provider', 'hospital']
        
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
    
# Class Managers
class PatientManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(type=User.UserType.PATIENT)

class HealthcareProviderManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(type=User.UserType.HEALTHCARE_PROVIDER)

class AdminStaffManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(type=User.UserType.ADMIN_STAFF)

class SystemAdminManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(type=User.UserType.SYSTEM_ADMIN)

# Proxy models
class Patient(User):
    objects = PatientManager() # type: ignore
    
    class Meta(User.Meta):
        proxy = True
        
    def save(self, *args, **kwargs):
        if not self.pk:
            self.type = User.UserType.PATIENT
        super().save(*args, **kwargs)
    
    @property
    def profile(self):
        return self.patient_profile # type: ignore
    
class HealthcareProvider(User):
    objects = HealthcareProviderManager() # type: ignore
    
    class Meta(User.Meta):
        proxy = True
        
    def save(self, *args, **kwargs):
        if not self.pk:
            self.type = User.UserType.HEALTHCARE_PROVIDER
        super().save(*args, **kwargs)
        
    @property
    def profile(self):
        return self.healthcare_provider_profile # type: ignore
    
class AdminStaff(User):
    objects = AdminStaffManager() # type: ignore
    
    class Meta(User.Meta):
        proxy = True
        
    def save(self, *args, **kwargs):
        if not self.pk:
            self.type = User.UserType.ADMIN_STAFF
        super().save(*args, **kwargs)
    
class SystemAdmin(User):
    objects = SystemAdminManager() # type: ignore
    
    class Meta(User.Meta):
        proxy = True
        
    def save(self, *args, **kwargs):
        if not self.pk:
            self.type = User.UserType.SYSTEM_ADMIN
        super().save(*args, **kwargs)
    
# Misc tables
class Appointment(BaseModel):
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
    location = models.CharField(max_length=255) # storing location as string in case of hospital data modification
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    
    class Meta(BaseModel.Meta):
        unique_together = ('patient', 'healthcare_provider', 'appointment_start_datetime_utc')
        constraints = [
            models.CheckConstraint(
                name='appointment_end_datetime_utc_gt_start_datetime',
                check=models.Q(appointment_end_datetime_utc__gt=models.F('appointment_start_datetime_utc'))
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
    
class MedicalRecord(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="medical_records")
    healthcare_provider = models.ForeignKey(HealthcareProvider, on_delete=models.CASCADE)
    diagnosis = models.TextField()
    notes = models.TextField()
    prescriptions = models.TextField()
    
    class Meta(BaseModel.Meta):
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Medical Record: {self.patient} - {self.updated_at}"
    
class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-sent_at']
    
    def clean(self):
        super().clean()
        
        if not self.content.strip():
            raise ValueError("Cannot send message without content")    
    
    def __str__(self):
        return f"Message from {self.sender} to {self.recipient}"
    
class Availability(models.Model):
    class DaysOfWeek(models.TextChoices):
        MONDAY = "MON", "Monday"
        TUESDAY = "TUE", "Tuesday"
        WEDNESDAY = "WED", "Wednesday"
        THURSDAY = "THU", "Thursday"
        FRIDAY = "FRI", "Friday"
        SATURDAY = "SAT", "Saturday"
        SUNDAY = "SUN", "Sunday"
    
    healthcare_provider = models.ForeignKey(HealthcareProvider, on_delete=models.CASCADE, related_name="availability_slots")
    day_of_week = models.CharField(max_length=3, choices=DaysOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    class Meta:
        unique_together = ('healthcare_provider', 'day_of_week')
        
    def __str__(self):
        return f"{self.healthcare_provider} Availability: {self.get_day_of_week_display()} {self.start_time}-{self.end_time}" # type: ignore
    
class TimeOff(models.Model):
    healthcare_provider = models.ForeignKey(HealthcareProvider, on_delete=models.CASCADE, related_name="provider_timeoff")
    start_datetime_utc = models.DateTimeField()
    end_datetime_utc = models.DateTimeField()
    
    class Meta:
        unique_together = ('healthcare_provider', 'start_datetime_utc')
        constraints = [
            models.CheckConstraint(
                name='timeoff_start_datetime_utc',
                check=models.Q(end_datetime_utc__gte=models.F('start_datetime_utc'))
            )
        ]
        ordering = ['-start_datetime_utc']
        
    def __str__(self):
        return f"{self.healthcare_provider} off: {self.start_datetime_utc} to {self.end_datetime_utc}"
