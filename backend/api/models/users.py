import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _

from ..mixin import TimestampMixin
from .managers import (
    PatientManager,
    HealthcareProviderManager,
    AdminStaffManager,
    SystemAdminManager
)

class User(TimestampMixin, AbstractUser):
    class UserType(models.TextChoices):
        PATIENT = "PATIENT", "Patient"
        HEALTHCARE_PROVIDER = "HEALTHCARE_PROVIDER", "Healthcare Provider"
        ADMIN_STAFF = "ADMIN_STAFF", "Admin Staff"
        SYSTEM_ADMIN = "SYSTEM_ADMIN", "System Admin"
        
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    email = models.EmailField(
        _("email address"),
        unique=True,
        error_messages={
            "unique": _("A user with this email already exists."),
        },
    )
    # Make first_name & last_name required
    first_name = models.CharField(_("first name"), max_length=150, blank=False)
    last_name  = models.CharField(_("last name"),  max_length=150, blank=False)

    base_type = UserType.PATIENT
    type = models.CharField(
        _("Type"), max_length=50, choices=UserType.choices, default=base_type
    )
    
    date_of_birth = models.DateField(_("Date of Birth"), null=True, blank=True)
    phone_number = models.CharField(_("Phone Number"), max_length=20, blank=True)
    address = models.TextField(_("Address"), blank=True)

    # Use email as username for login
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    # Enforce case insensitive uniqueness
    class Meta(TimestampMixin.Meta):
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                name="user_email_ci_unique"
            )
        ]

    def __str__(self):
        return f"{self.username}: {self.get_type_display()}"
    
class Patient(User):
    objects = PatientManager()
    
    class Meta(User.Meta):
        proxy = True
        
    def save(self, *args, **kwargs):
        if not self.pk:
            self.type = User.UserType.PATIENT
        super().save(*args, **kwargs)
    
    @property
    def profile(self):
        return self.patient_profile
    
class HealthcareProvider(User):
    objects = HealthcareProviderManager()
    
    class Meta(User.Meta):
        proxy = True
        
    def save(self, *args, **kwargs):
        if not self.pk:
            self.type = User.UserType.HEALTHCARE_PROVIDER
        super().save(*args, **kwargs)
        
    @property
    def profile(self):
        return self.healthcare_provider_profile 
    
class AdminStaff(User):
    objects = AdminStaffManager() 
    
    class Meta(User.Meta):
        proxy = True
        
    def save(self, *args, **kwargs):
        if not self.pk:
            self.type = User.UserType.ADMIN_STAFF
        super().save(*args, **kwargs)
    
class SystemAdmin(User):
    objects = SystemAdminManager() 
    
    class Meta(User.Meta):
        proxy = True
        
    def save(self, *args, **kwargs):
        if not self.pk:
            self.type = User.UserType.SYSTEM_ADMIN
        super().save(*args, **kwargs)