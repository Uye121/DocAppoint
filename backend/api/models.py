from typing import List, Optional
from datetime import datetime, timedelta
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import UserManager, AbstractUser, PermissionsMixin, Group
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
    
    def save(self, *args, **kwargs):
        if self._state.adding: # Check if it's a new object
            self.type = self.base_type
        return super().save(*args, **kwargs)
    
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
    weight = models.PositiveIntegerField(_("Weight (grams)"), blank=True, null=True, help_text="Weight in grams")
    height = models.PositiveIntegerField(_("Height (cm)"), blank=True, null=True, help_text="Height in centimeters")
    
    def __str__(self):
        return f"Patient Profile: {self.user.username}"
    
class HealthcareProviderProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="healthcare_provider_profile")
    speciality = models.ForeignKey(Speciality, on_delete=models.CASCADE, related_name='doctors')
    image = models.ImageField(upload_to='doctors')
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
        
class AdminStaffProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="admin_staff_profile")
    
    # Affiliation
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='admin_staff')
    
    def __str__(self):
        return f"Admin Staff: {self.user.username} - {self.hospital.name}"
    
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
    
class Patient(User):
    base_type = User.UserType.PATIENT
    objects = PatientManager() # type: ignore
    
    class Meta: # type: ignore
        proxy = True
    
    @property
    def profile(self):
        return self.patient_profile # type: ignore
    
    def view_doctors(self):
        return HealthcareProvider.objects.all()
    
    def search_doctors(self, speciality:'Speciality | None'=None):
        queryset = HealthcareProvider.objects.all()
        
        if speciality:
            queryset = queryset.filter(
                healthcare_provider_profile__speciality__name__icontains=speciality
            )
        return queryset
    
    def schedule_appointment(self, doctor:'HealthcareProvider', date_time:datetime, reason:str):
        try:
            return Appointment.objects.create(
                patient=self,
                healthcare_provider=doctor,
                appointment_date=date_time,
                reason=reason,
                status=Appointment.Status.REQUESTED,
            )
        except (ValidationError, ValueError) as e:
            raise e
    
    def view_appointments(self, upcoming:bool=True, status:str | list | None=None, limit:int | None=None):
        now = timezone.now()
        queryset = self.patient_appointments.all() # type: ignore

        if upcoming:
            queryset = queryset.filter(appointment_date__gte=now)
        else:
            queryset = queryset.filter(appointment_date__lt=now)
            
        if status:
            if isinstance(status, str):
                queryset = queryset.filter(status=status)
            elif isinstance(status, list):
                queryset = queryset.filter(status__in=status)
        
        order = 'appointment_date' if upcoming else '-appointment_date'
        queryset = queryset.order_by(order)
        
        if limit:
            queryset = queryset[:limit]
            
        return queryset
    
    def view_medical_records(self, date_range:List[datetime] | None=None, provider:'HealthcareProvider | None'=None, limit:int | None=None):
        queryset = self.medical_records.all() # type: ignore
        
        if date_range: # [start_date, end_date]
            queryset = queryset.filter(record_date__range=date_range)
            
        if provider:
            queryset = queryset.filter(healthcare_provider=provider)
            
        if limit:
            queryset = queryset[:limit]
        
        return queryset
    
    def send_message(self, recipient: 'User', subject:str, message:str):
        if not recipient.is_active:
            raise ValueError("Cannot send message to inactivate user")
        
        if not subject.strip():
            raise ValueError("Subject cannot be empty")
        
        if not message.strip():
            raise ValueError("Message cannot be empty")

        return Message.objects.create(
            sender=self,
            recipient=recipient,
            subject=subject,
            message=message
        )
    
class HealthcareProvider(User):
    base_type = User.UserType.HEALTHCARE_PROVIDER
    objects = HealthcareProviderManager() # type: ignore
    
    class Meta: # type: ignore
        proxy = True
        
    @property
    def profile(self):
        return self.healthcare_provider_profile # type: ignore
    
    def set_availability(self, start_time: datetime, end_time: datetime, days_of_week: str | List[str]):
        self.availability_slots.filter(days_of_week__in=days_of_week) # type: ignore
        
        for day in days_of_week:
            Availability.objects.create(
                healthcare_provider=self,
                days_of_week=day,
                start_time=start_time,
                end_time=end_time
            )
            
    def set_timeoff(self, start_datetime: datetime, end_datetime: datetime):
        now = timezone.now()
        
        if now < start_datetime or now < end_datetime:
            raise ValueError("Cannot set time off at a past datetime")
        
        return TimeOff.objects.create(
            healthcare_provider=self,
            start_datetime=start_datetime,
            end_datetime=end_datetime
        )
    
    def view_appointment_schedule(self, view_type: str='day'):
        now = timezone.now()
        
        if view_type not in ['day', 'week', 'month']:
            raise ValueError("view_type can only be day, week, and month.")
        
        start_date = now.date()
        end_date = now.date()
        
        match view_type:
            case 'day':
                pass
            case 'week':
                start_date = now.date() - timedelta(days=now.weekday())
                end_date = start_date + timedelta(days=6)
            case 'month':
                start_date = now.date().replace(day=1)
                next_month = start_date.replace(day=28) + timedelta(days=4)
                end_date = next_month - timedelta(days=next_month.day)
                
        return self.provider_appointments.filter( # type: ignore
            appointment_date__date__range=[start_date, end_date]
        )
    
    def accept_appointment(self, appointment: 'Appointment'):
        if appointment.healthcare_provider != self:
            raise PermissionError("Cannot accept appointments scheduled for other providers.")
        
        if appointment.status != Appointment.Status.REQUESTED:
            raise ValueError("Can only accept requested appointments.")
        
        appointment.status = Appointment.Status.CONFIRMED
        appointment.save()
        
        # Confirmation message to the patient
        msg = f"""
        Dear {appointment.patient.first_name},

        Your appointment with Dr. {self.last_name} has been confirmed.

        📅 Date: {appointment.appointment_date.strftime('%A, %B %d, %Y')}
        ⏰ Time: {appointment.appointment_date.strftime('%I:%M %p')}
        📍 Location: {appointment.location or 'Our Medical Center'}

        Please arrive 15 minutes early for your appointment. If you need to reschedule or cancel, please contact us at least 24 hours in advance.

        We look forward to seeing you!

        Best regards,
        Dr. {self.last_name}'s Office
        """
        self.send_message(appointment.patient, "Confirmation " + str(appointment), msg)
        
        return appointment
    
    def add_medical_record(self, patient: Patient, diagnosis: str, notes: str,
                           prescriptions: str):
        return MedicalRecord(
            patient=patient,
            healthcare_provider=self,
            diagnosis=diagnosis,
            notes=notes,
            prescriptions=prescriptions
        )
    
    def send_message(self, recipient: User, subject: str, message:str):
        if not recipient.is_active:
            raise ValueError("Cannot send message to inactivate user")
        
        if not subject.strip():
            raise ValueError("Subject cannot be empty")
        
        if not message.strip():
            raise ValueError("Message cannot be empty")

        return Message.objects.create(
            sender=self,
            recipient=recipient,
            subject=subject,
            message=message
        )
    
class AdminStaff(User):
    base_type = User.UserType.ADMIN_STAFF
    objects = AdminStaffManager() # type: ignore
    
    class Meta: # type: ignore
        proxy = True
        
    def manage_appointment(self, appointment: 'Appointment', action: str, **kwargs): 
        # Check if appointment is with healthcare provider the admin staff
        # manages.
        admin_hospital = self.admin_staff_profile.hospital # type: ignore
        healthcare_provider = appointment.healthcare_provider
        is_affiliated = (
            healthcare_provider.hospitals.filter(id=admin_hospital.id).exists() or # type: ignore
            healthcare_provider.primary_hospital == admin_hospital # type: ignore
        )
        
        if not is_affiliated:
            raise PermissionError("Cannot manage appointments from another hospital.")
        
        if action == 'reschedule':
            new_date = kwargs.get('new_date')
            if new_date is None:
                raise ValueError("new_date parameter is required for rescheduling.")
            if not isinstance(new_date, datetime):
                raise TypeError("new_date must be a datetime object.")

            appointment.appointment_date = new_date
            appointment.status = Appointment.Status.RESCHEDULED
        elif action == 'cancel':
            appointment.status = Appointment.Status.CANCELLED
        elif action == 'complete':
            appointment.status = Appointment.Status.COMPLETED
        else:
            raise ValueError("Unknown action.")
        
        appointment.save()
        return appointment
    
    def view_all_patients(self):
        return Patient.objects.all()
    
class SystemAdmin(User):
    base_type = User.UserType.SYSTEM_ADMIN
    objects = SystemAdminManager() # type: ignore
    
    class Meta: # type: ignore
        proxy = True
        
    def create_user_account(self, username: str, password: str, email: str, user_type: User.UserType, **extra_fields):
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            type=user_type,
            **extra_fields
        )
        
        match user_type:
            case User.UserType.PATIENT:
                PatientProfile.objects.create(user=user)
            case User.UserType.HEALTHCARE_PROVIDER:
                HealthcareProviderProfile.objects.create(user=user)
            case User.UserType.ADMIN_STAFF:
                AdminStaffProfile.objects.create(user=user)

        return user
    
    def disable_user_account(self, user: User):
        user.is_active = False
        user.save()
        return user
    
    def assign_role(self, user: User, group_name: str):
        group, created = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
        return user
    
    def reset_password(self, user: User, new_password: str):
        user.set_password(new_password)
        user.save()
        return user
    
class Appointment(BaseModel, models.Model):
    class Status(models.TextChoices):
        REQUESTED = "REQUESTED", "Requested"
        CONFIRMED = "CONFIRMED", "Confirmed"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        RESCHEDULED = "RESCHEDULED", "Rescheduled"
        
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="patient_appointments")
    healthcare_provider = models.ForeignKey(HealthcareProvider, on_delete=models.CASCADE, related_name="provider_appointments")
    appointment_date = models.DateTimeField()
    location = models.CharField(max_length=255)
    comment = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    
    def clean(self):
        super().clean()
        
        if self.appointment_date and self.appointment_date < timezone.now():
            raise ValidationError({'appointment_date': 'Cannot schedule an appointment for a past date.'})
        
    class Meta: # type: ignore
        constraints = [
            models.CheckConstraint(
                name='appointment_date_cannot_be_in_the_past',
                check=models.Q(appointment_date__gte=timezone.now()),
                violation_error_message='Appointment date must be in the future.'
            )
        ]
    
    def __str__(self):
        return f"Appointment: {self.patient} with {self.healthcare_provider} on {self.appointment_date}"
    
class MedicalRecord(BaseModel, models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="medical_records")
    healthcare_provider = models.ForeignKey(HealthcareProvider, on_delete=models.CASCADE)
    diagnosis = models.TextField()
    notes = models.TextField()
    prescriptions = models.TextField()
    
    def __str__(self):
        return f"Medical Record: {self.patient} - {self.updated_at}"
    
class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
    subject = models.CharField(max_length=255)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Message from {self.sender} to {self.recipient} on {self.subject}"
    
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
    healthcare_provider = models.ForeignKey(HealthcareProvider, on_delete=models.CASCADE, related_name="time_off")
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                name='end_date_after_start_date',
                check=models.Q(end_date__gte=models.F('start_date'))
            )
        ]
        
    def __str__(self):
        return f"{self.healthcare_provider} off: {self.start_datetime} to {self.end_datetime}"
