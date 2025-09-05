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
    
    def send_message(self, recipient: 'User', content: str) -> 'Message':
        if not recipient.is_active:
            raise ValueError("Cannot send message to inactivate user")
        
        if not content.strip():
            raise ValueError("Message cannot be empty")

        return Message.objects.create(
            sender=self,
            recipient=recipient,
            content=content
        )
        
    def view_message(self,
                     other_user: Optional['User'] = None,
                     limit:int = 50,
                     unread_only: bool = False) -> List['Message']:
        
        sent = self.sent_messages.all() # type: ignore
        received = self.received_messages.all() # type: ignore
        
        if other_user:
            sent = sent.filter(
                models.Q(sender=other_user) | models.Q(recipient=other_user) # type: ignore
            )
            received = received.filter(
                models.Q(sender=other_user) | models.Q(recipient=other_user) # type: ignore
            )
            
        if unread_only:
            sent = sent.filter(read=False)
            received = received.filter(read=False)
        
        queryset = sent.union(received)
        queryset = queryset.order_by('-sent_at')
        
        return queryset.all()[:limit]
    
    def get_conversation(self, other_user: 'User', limit: int = 50) -> List['Message']:
        return self.view_message(other_user=other_user, limit=limit)
    
    def get_unread_count(self, other_user: Optional['User'] = None) -> int:
        queryset = self.received_messages.filter(read=False) # type: ignore
        
        if other_user:
            queryset = queryset.filter(sender=other_user)
        
        return queryset.count()
    
    def mark_as_read(self, messages: Optional[List['Message']] = None,
                     other_user: Optional['User'] = None):
        if messages:
            for message in messages:
                if message.recipient != self:
                    raise PermissionError("Cannot mark other user's message as read")
                message.read = True
                message.save()
        elif other_user:
            self.received_messages.filter(sender=other_user, read=False).update(read=True) # type: ignore
    
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
    
    class Meta: # type: ignore
        proxy = True
        
    def save(self, *args, **kwargs):
        if not self.pk:
            self.type = User.UserType.PATIENT
        super().save(*args, **kwargs)
    
    @property
    def profile(self):
        return self.patient_profile # type: ignore
    
    def view_healthcare_providers(self) -> QuerySet:
        return HealthcareProvider.objects.all()
    
    def search_healthcare_providers(self, speciality: Optional[Speciality]=None) -> QuerySet:
        queryset = HealthcareProvider.objects.all()
        
        if speciality:
            queryset = queryset.filter(
                healthcare_provider_profile__speciality__name__icontains=speciality
            )
        return queryset
    
    def schedule_appointment(self, healthcare_providers:'HealthcareProvider',
                             start_datetime_utc: datetime, end_datetime_utc: datetime,
                             reason:str, location: Optional[str]=None) -> 'Appointment':
        try:
            if location is None:
                profile = healthcare_providers.healthcare_provider_profile # type: ignore
                location = profile.primary_hospital.address
            appointment = Appointment.objects.create(
                patient=self,
                healthcare_provider=healthcare_providers,
                appointment_start_datetime_utc=start_datetime_utc,
                appointment_end_datetime_utc=end_datetime_utc,
                location=location,
                reason=reason,
                status=Appointment.Status.REQUESTED,
            )
            appointment.full_clean()
            appointment.save()
            
            return appointment
        except (ValidationError, ValueError) as e:
            raise e
    
    def view_appointments(self, upcoming: Optional[bool]=None,
                          status: Union[str, list, None]=None,
                          limit: Optional[int]=None) -> QuerySet:
        now = timezone.now()
        queryset = self.patient_appointments.all() # type: ignore

        if upcoming:
            queryset = queryset.filter(appointment_end_datetime_utc__gte=now)
        elif upcoming == False:
            queryset = queryset.filter(appointment_end_datetime_utc__lt=now)
            
        if status:
            if isinstance(status, str):
                queryset = queryset.filter(status=status)
            elif isinstance(status, list):
                queryset = queryset.filter(status__in=status)
        
        order = 'appointment_start_datetime_utc' if upcoming else '-appointment_start_datetime_utc'
        queryset = queryset.order_by(order)
        
        if limit:
            queryset = queryset[:limit]
            
        return queryset
    
    def view_medical_records(self, date_range: Optional[List[datetime]]=None,
                             provider:Optional['HealthcareProvider']=None,
                             limit: Optional[int]=None) -> QuerySet:
        queryset = self.medical_records.all() # type: ignore
        
        if date_range: # [start_date, end_date]
            queryset = queryset.filter(record_date__range=date_range)
            
        if provider:
            queryset = queryset.filter(healthcare_provider=provider)
            
        if limit:
            queryset = queryset[:limit]
        
        return queryset
    
class HealthcareProvider(User):
    objects = HealthcareProviderManager() # type: ignore
    
    class Meta: # type: ignore
        proxy = True
        
    def save(self, *args, **kwargs):
        if not self.pk:
            self.type = User.UserType.HEALTHCARE_PROVIDER
        super().save(*args, **kwargs)
        
    @property
    def profile(self):
        return self.healthcare_provider_profile # type: ignore
    
    def _validate_day(self, day: str):
        valid_days = [choice[0] for choice in Availability.DaysOfWeek.choices]
        if day not in valid_days:
            raise ValueError(f"Invalid day of week: {day}. Must be one of {valid_days}")
        
    def _validate_time(self, start_time: datetime, end_time: datetime):
        if start_time >= end_time:
            raise ValueError("Start time must be before end time")
    
    def set_availability(self, slots: Dict[str, tuple[datetime, ...]]) -> List['Availability']:
        # validate time slots
        for day, (start_time, end_time) in slots.items():
            self._validate_day(day)
            self._validate_time(start_time, end_time)
                
        for day, (start_time, end_time) in slots.items():
            Availability.objects.update_or_create(
                healthcare_provider=self,
                day_of_week=day,
                start_time=start_time,
                end_time=end_time
            )
            
        valid_days = {choice[0] for choice in Availability.DaysOfWeek.choices}
        remaining_days = valid_days - set(slots.keys()) # type: ignore
        self.remove_availability(list(remaining_days))

        return self.availability_slots.all() # type: ignore
    
    def remove_availability(self, days_of_week: List[str]) -> int:
        for day in days_of_week:
            self._validate_day(day)
            
        count, _ = self.availability_slots.filter(day_of_week__in=days_of_week).delete() # type: ignore
        return count
            
    def set_timeoff(self, start_datetime_utc: datetime, end_datetime_utc: datetime) -> 'TimeOff':
        now = timezone.now()
        
        if end_datetime_utc < now:
            raise ValueError("Cannot set time off for a past time")
        
        if start_datetime_utc >= end_datetime_utc:
            raise ValueError("Start time must be before end datetime")
        
        return TimeOff.objects.create(
            healthcare_provider=self,
            start_datetime_utc=start_datetime_utc,
            end_datetime_utc=end_datetime_utc
        )
        
    def view_timeoff(self, upcoming: Optional[bool] = None) -> QuerySet:
        now = timezone.now()
        queryset = self.provider_timeoff.all() # type: ignore
        
        if upcoming is True:
            return queryset.filter(start_datetime_utc__gt=now)
        elif upcoming is False:
            return queryset.filter(start_datetime_utc__lt=now)
        else:
            return queryset
    
    def view_appointment_schedule(self, view_type: str='day') -> QuerySet:
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
            appointment_start_datetime_utc__date__range=[start_date, end_date]
        )
    
    def accept_appointment(self, appointment: 'Appointment') -> 'Appointment':
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

        📅 Date: {appointment.appointment_start_datetime_utc.strftime('%A, %B %d, %Y')}
        ⏰ Time: {appointment.appointment_start_datetime_utc.strftime('%I:%M %p')}
        📍 Location: {appointment.location or 'Our Medical Center'}

        Please arrive 15 minutes early for your appointment. If you need to reschedule or cancel, please contact us at least 24 hours in advance.

        We look forward to seeing you!

        Best regards,
        Dr. {self.last_name}'s Office
        """
        self.send_message(appointment.patient, msg)
        
        return appointment
    
    def add_medical_record(self, patient: Patient, diagnosis: str, notes: str,
                           prescriptions: str) -> 'MedicalRecord':
        if not diagnosis.strip():
            raise ValueError("Cannot have empty diagnosis")
        if not notes.strip():
            raise ValueError("Cannot have empty notes")
        if not prescriptions.strip():
            raise ValueError("Cannot have empty prescriptions")
        
        medical_record = MedicalRecord(
            patient=patient,
            healthcare_provider=self,
            diagnosis=diagnosis,
            notes=notes,
            prescriptions=prescriptions
        )
        medical_record.save()
        return medical_record
    
class AdminStaffProvider(User):
    objects = AdminStaffManager() # type: ignore
    
    class Meta: # type: ignore
        proxy = True
        
    def save(self, *args, **kwargs):
        if not self.pk:
            self.type = User.UserType.ADMIN_STAFF
        super().save(*args, **kwargs)
        
    def manage_appointment(self, appointment: 'Appointment', action: str, **kwargs) -> 'Appointment':
        # Check if appointment is with healthcare provider the admin staff
        # manages.
        admin_hospital = self.admin_staff_profile.hospital # type: ignore
        healthcare_provider = appointment.healthcare_provider

        is_affiliated = False
        if healthcare_provider and healthcare_provider.healthcare_provider_profile: # type: ignore
            profile = healthcare_provider.healthcare_provider_profile # type: ignore
            
            if profile.hospitals.filter(id=admin_hospital.id).exists():
                is_affiliated = True
            elif profile.primary_hospital and profile.primary_hospital.id == admin_hospital.id:
                is_affiliated = True
        
        if not is_affiliated:
            raise PermissionError("Cannot manage appointments from another hospital.")
        
        if action == 'reschedule':
            new_start_datetime = kwargs.get('new_start_datetime')
            new_end_datetime = kwargs.get('new_end_datetime')
            if new_start_datetime is None or new_end_datetime is None:
                raise ValueError("new_start_datetime and new_end_datetime parameter is required for rescheduling.")
            if not isinstance(new_start_datetime, datetime) or not isinstance(new_end_datetime, datetime):
                raise TypeError("new_date must be a datetime object.")

            appointment.appointment_start_datetime_utc = new_start_datetime
            appointment.appointment_end_datetime_utc = new_end_datetime
            appointment.status = Appointment.Status.RESCHEDULED
        elif action == 'cancel':
            appointment.status = Appointment.Status.CANCELLED
        elif action == 'complete':
            appointment.status = Appointment.Status.COMPLETED
        else:
            raise ValueError("Unknown action.")
        
        appointment.save()
        return appointment
    
    def view_all_patients(self) -> QuerySet:
        return Patient.objects.all()
    
class SystemAdmin(User):
    objects = SystemAdminManager() # type: ignore
    
    class Meta: # type: ignore
        proxy = True
        
    def save(self, *args, **kwargs):
        if not self.pk:
            self.type = User.UserType.SYSTEM_ADMIN
        super().save(*args, **kwargs)
        
    def create_user_account(self, username: str, password: str, email: str,
                            user_type: User.UserType, **extra_fields) -> User:
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
    
    def disable_user_account(self, user: User) -> User:
        user.is_active = False
        user.save()
        return user
    
    def assign_role(self, user: User, group_name: str) -> User:
        group, created = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
        return user
    
    def reset_password(self, user: User, new_password: str) -> User:
        user.set_password(new_password)
        user.save()
        return user
    
# Misc tables
class Appointment(BaseModel, models.Model):
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
    
    class Meta: # type: ignore
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
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    
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
        
    def __str__(self):
        return f"{self.healthcare_provider} off: {self.start_datetime_utc} to {self.end_datetime_utc}"
