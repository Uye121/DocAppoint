import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.functions import Lower
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinLengthValidator, RegexValidator

from ..mixin import TimestampMixin
from .hospital import Hospital
from .speciality import Speciality


class User(TimestampMixin, AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(
        _("email address"),
        unique=True,
        error_messages={
            "unique": _("A user with this email already exists."),
        },
    )
    # Make first_name & last_name required
    first_name = models.CharField(
        _("first name"), max_length=150, blank=False, validators=[MinLengthValidator(1)]
    )
    last_name = models.CharField(
        _("last name"), max_length=150, blank=False, validators=[MinLengthValidator(1)]
    )
    date_of_birth = models.DateField(_("Date of Birth"), null=True, blank=True)
    phone_number = models.CharField(_("Phone Number"), max_length=20, blank=True)
    address_line1 = models.CharField("Address line 1", max_length=1024, blank=True)
    address_line2 = models.CharField("Address line 2", max_length=1024, blank=True)
    city = models.CharField(max_length=50, blank=True)
    state = models.CharField(max_length=2, blank=True)
    zip_code = models.CharField(max_length=5, blank=True)
    image = models.ImageField(upload_to="users_images", blank=True, null=True)
    reset_sent_at = models.DateTimeField(null=True, blank=True)

    # Use email as username for login
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    # Enforce case insensitive uniqueness
    class Meta(TimestampMixin.Meta):
        constraints = [
            models.UniqueConstraint(Lower("email"), name="user_email_ci_unique")
        ]

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Patient(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient",
        primary_key=True,
    )
    blood_type = models.CharField(_("Blood Type"), max_length=5, blank=True)
    allergies = models.TextField(_("Allergies"), blank=True)
    chronic_conditions = models.TextField(_("Chronic Conditions"), blank=True)
    current_medications = models.TextField(_("Current Medications"), blank=True)
    insurance = models.CharField(_("Insurance"), max_length=255, blank=True)
    weight = models.PositiveIntegerField(
        _("Weight (kg)"), blank=True, null=True, help_text="Weight in kg"
    )
    height = models.PositiveIntegerField(
        _("Height (cm)"), blank=True, null=True, help_text="Height in cm"
    )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class HealthcareProvider(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="provider",
        primary_key=True,
    )
    speciality = models.ForeignKey(
        Speciality,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="provider_speciality",
    )
    education = models.TextField(_("Education"), blank=True)
    years_of_experience = models.PositiveIntegerField(
        _("Years of Experience"), default=0
    )
    about = models.TextField()
    fees = models.DecimalField(max_digits=9, decimal_places=2)
    address_line1 = models.CharField("Address line 1", max_length=1024)
    address_line2 = models.CharField("Address line 2", max_length=1024, blank=True)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=2)
    zip_code = models.CharField(max_length=5)

    license_validator = RegexValidator(
        regex=r"^[A-Z0-9]{6,20}$",
        message="License must be 6-20 alphanumeric characters.",
    )

    license_number = models.CharField(
        _("License Number"), max_length=100, validators=[license_validator]
    )
    certifications = models.TextField(_("Certifications"), blank=True)

    # Affiliations
    hospitals = models.ManyToManyField(Hospital, through="ProviderHospitalAssignment")
    primary_hospital = models.ForeignKey(
        Hospital,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="primary_provider",
    )

    # Attributes for soft-delete
    is_removed = models.BooleanField(default=False, db_index=True)
    removed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "api_healthcareprovider"
        verbose_name = _("Healthcare Provider")
        verbose_name_plural = _("Healthcare Providers")
        constraints = [
            models.CheckConstraint(
                name="experience_non_negative",
                condition=models.Q(years_of_experience__gte=0),
            ),
            models.CheckConstraint(name="fees_above_0", condition=models.Q(fees__gt=0)),
            models.CheckConstraint(
                name="valid_license_format",
                condition=models.Q(license_number__regex=r"^[A-Z0-9]{6,20}$"),
            ),
        ]


class AdminStaff(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="admin_staff",
        primary_key=True,
    )
    # Affiliation
    hospital = models.ForeignKey(
        Hospital, on_delete=models.CASCADE, related_name="hospital"
    )

    class Meta:
        db_table = "api_adminstaff"
        verbose_name = _("Admin Staff")
        verbose_name_plural = _("Admin Staff")


class SystemAdmin(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="system_admin",
        primary_key=True,
    )
    role = models.CharField(max_length=50)

    class Meta:
        db_table = "api_systemadmin"
        verbose_name = _("System Admin")
        verbose_name_plural = _("System Admins")

    def delete(self, *args, **kwargs):
        self.user.is_staff = False
        self.user.save()
        super().delete(*args, **kwargs)
