# from typing import List, Optional, Union, Dict
# from datetime import datetime, timedelta
# from django.utils import timezone
# from django.contrib.auth.models import Group
# from django.db import models
# from django.db.models.query import QuerySet
# from django.core.exceptions import ValidationError
# from .models import (
#     User, Message, Patient, HealthcareProvider, Speciality,
#     Appointment, MedicalRecord, AdminStaff,
#     HealthcareProviderProfile, PatientProfile, AdminStaffProfile
# )

# class HealthcareProviderService:
#     @staticmethod
#     def get_all_providers() -> QuerySet:
#         return HealthcareProvider.objects.all()

#     @staticmethod
#     def get_providers_by_speciality(speciality: Speciality) -> QuerySet:
#         return HealthcareProvider.objects.filter(speciality=speciality)

# class AdminStaffService:
#     @staticmethod
#     def view_all_patients() -> QuerySet:
#         # TODO: change it to view patients who visited their hospital
#         return Patient.objects.all()

# class SystemAdminService:
#     @staticmethod
#     def create_user_account(username: str, password: str, email: str,
#                             type: User.UserType, **extra_fields) -> tuple[User,
#                                                                           HealthcareProviderProfile
#                                                                           | PatientProfile
#                                                                           | AdminStaffProfile]:
#         if type not in [User.UserType.PATIENT, User.UserType.HEALTHCARE_PROVIDER, User.UserType.ADMIN_STAFF]:
#             raise ValidationError("Invalid user type")
#         if type == User.UserType.HEALTHCARE_PROVIDER:
#             req_attribute = ['speciality', 'image', 'education', 'about',
#                             'years_of_experience', 'fees', 'address_line1',
#                             'city', 'state', 'zip_code', 'license_number']
#             for attr in req_attribute:
#                 if attr not in extra_fields:
#                     raise ValidationError(f'Mising one of the required attributes: {req_attribute}')
#         if type == User.UserType.ADMIN_STAFF:
#             if 'hospital' not in extra_fields:
#                 raise ValidationError('Missing required attribute "hospital"')


#         user = User.objects.create_user(
#             username=username,
#             password=password,
#             email=email,
#             type=type,
#             first_name=extra_fields.pop("first_name"),
#             last_name=extra_fields.pop("last_name")
#         )

#         match type:
#             case User.UserType.PATIENT:
#                 profile = PatientProfile.objects.create(
#                     user=user,
#                     **extra_fields
#                 )
#             case User.UserType.HEALTHCARE_PROVIDER:
#                 profile = HealthcareProviderProfile.objects.create(
#                     user=user,
#                     **extra_fields
#                 )
#             case User.UserType.ADMIN_STAFF:
#                 profile = AdminStaffProfile.objects.create(
#                     user=user,
#                     **extra_fields
#                 )
#             # Create patient by default
#             case _:
#                 profile = PatientProfile.objects.create(
#                     user=user,
#                     **extra_fields
#                 )

#         return user, profile

#     @staticmethod
#     def disable_user_account(user: User) -> User:
#         user.is_active = False
#         user.save()
#         return user

#     @staticmethod
#     def assign_role(user: User, group_name: str) -> User:
#         group, _ = Group.objects.get_or_create(name=group_name)
#         user.groups.add(group)
#         return user

#     @staticmethod
#     def reset_password(user: User, new_password: str) -> User:
#         user.set_password(new_password)
#         user.save()
#         return user

# class MessageService:
#     def __init__(self, user: User):
#         self.user = user

#     def send_message(self, recipient: User, content: str) -> Message:
#         if not recipient.is_active:
#             raise ValueError("Cannot send message to inactivate user")

#         if not content.strip():
#             raise ValueError("Message cannot be empty")

#         return Message.objects.create(
#             sender=self.user,
#             recipient=recipient,
#             content=content
#         )

#     def view_message(self,
#                      other_user: Optional['User'] = None,
#                      limit:int = 50,
#                      unread_only: bool = False) -> QuerySet:

#         queryset = Message.objects.filter(
#             models.Q(sender=self.user) | models.Q(recipient=self.user)
#         )

#         if other_user:
#             queryset = queryset.filter(
#                 models.Q(sender=other_user) | models.Q(recipient=other_user)
#             )

#         if unread_only:
#             queryset = queryset.filter(read=False)

#         queryset = queryset.order_by('-sent_at')

#         return queryset[:limit]

#     def get_conversation(self, other_user: User, limit: int = 50) -> QuerySet:
#         return self.view_message(other_user=other_user, limit=limit)

#     def get_unread_count(self, other_user: Optional[User] = None) -> int:
#         queryset = Message.objects.filter(read=False)

#         if other_user:
#             queryset = queryset.filter(sender=other_user)

#         return queryset.count()

#     def mark_as_read(self, messages: Optional[List[Message]] = None,
#                      other_user: Optional[User] = None):
#         if messages:
#             for message in messages:
#                 if message.recipient != self:
#                     raise PermissionError("Cannot mark other user's message as read")
#                 message.read = True
#                 message.save()
#         elif other_user:
#             Message.objects.filter(sender=other_user, read=False).update(read=True)
#         else:
#             Message.objects.filter(recipient=self.user, read=False).update(read=True)

# class PatientAppointmentService:
#     def __init__(self, patient: Patient):
#         self.patient = patient

#     def schedule_appointment(self, healthcare_providers:HealthcareProvider,
#                              start_datetime_utc: datetime, end_datetime_utc: datetime,
#                              reason:str, location: Optional[str]=None) -> Appointment:
#         if end_datetime_utc < start_datetime_utc:
#             raise ValueError("End time must be greater than start time.")

#         try:
#             if location is None:
#                 profile = healthcare_providers.healthcare_provider_profile # type: ignore
#                 location = profile.primary_hospital.address

#             appointment = Appointment.objects.create(
#                 patient=self.patient,
#                 healthcare_provider=healthcare_providers,
#                 appointment_start_datetime_utc=start_datetime_utc,
#                 appointment_end_datetime_utc=end_datetime_utc,
#                 location=location,
#                 reason=reason,
#                 status=Appointment.Status.REQUESTED,
#             )
#             appointment.full_clean()
#             appointment.save()

#             return appointment
#         except (ValidationError, ValueError) as e:
#             raise e

#     def view_appointments(self, upcoming: Optional[bool]=None,
#                           status: Union[str, list[str], None]=None,
#                           limit: Optional[int]=None) -> QuerySet:
#         queryset = self.patient.patient_appointments.all() # type: ignore
#         now = timezone.now()

#         if upcoming:
#             queryset = queryset.filter(appointment_end_datetime_utc__gte=now)
#         elif upcoming == False:
#             queryset = queryset.filter(appointment_end_datetime_utc__lt=now)

#         if status:
#             if isinstance(status, str):
#                 queryset = queryset.filter(status=status)
#             elif isinstance(status, list):
#                 queryset = queryset.filter(status__in=status)

#         order = 'appointment_start_datetime_utc' if upcoming else '-appointment_start_datetime_utc'
#         queryset = queryset.order_by(order)

#         if limit:
#             queryset = queryset[:limit]

#         return queryset

# class ProviderAppointmentService:
#     def __init__(self, provider: HealthcareProvider):
#         self.provider = provider

#     def schedule_appointment(self, patient: Patient,
#                              start_datetime_utc: datetime, end_datetime_utc: datetime,
#                              reason:str, location: Optional[str]=None) -> Appointment:
#         if end_datetime_utc < start_datetime_utc:
#             raise ValueError("End time must be greater than start time.")

#         try:
#             if location is None:
#                 profile = healthcare_providers.healthcare_provider_profile # type: ignore
#                 location = profile.primary_hospital.address
#             appointment = Appointment.objects.create(
#                 patient=patient,
#                 healthcare_provider=self.provider,
#                 appointment_start_datetime_utc=start_datetime_utc,
#                 appointment_end_datetime_utc=end_datetime_utc,
#                 location=location,
#                 reason=reason,
#                 status=Appointment.Status.REQUESTED,
#             )
#             appointment.full_clean()
#             appointment.save()

#             return appointment
#         except (ValidationError, ValueError) as e:
#             raise e

#     def view_appointment_schedule(self, view_type: str='day') -> QuerySet:
#         now = timezone.now()

#         if view_type not in ['day', 'week', 'month']:
#             raise ValueError("view_type can only be day, week, and month.")

#         start_date = now.date()
#         end_date = now.date()
#         match view_type:
#             case 'day':
#                 pass
#             case 'week':
#                 start_date = now.date() - timedelta(days=now.weekday())
#                 end_date = start_date + timedelta(days=6)
#             case 'month':
#                 start_date = now.date().replace(day=1)
#                 next_month = start_date.replace(day=28) + timedelta(days=4)
#                 end_date = next_month - timedelta(days=next_month.day)

#         return self.provider.provider_appointments.filter( # type: ignore
#             appointment_start_datetime_utc__date__range=[start_date, end_date]
#         )

#     def accept_appointment(self, appointment: 'Appointment') -> 'Appointment':
#         if appointment.healthcare_provider != self.provider:
#             raise PermissionError("Cannot accept appointments scheduled for other providers.")

#         if appointment.status != Appointment.Status.REQUESTED:
#             raise ValueError("Can only accept requested appointments.")

#         appointment.status = Appointment.Status.CONFIRMED
#         appointment.save()

#         # Confirmation message to the patient
#         msg = f"""
#         Dear {appointment.patient.first_name},

#         Your appointment with Dr. {self.provider.last_name} has been confirmed.

#         📅 Date: {appointment.appointment_start_datetime_utc.strftime('%A, %B %d, %Y')}
#         ⏰ Time: {appointment.appointment_start_datetime_utc.strftime('%I:%M %p')}
#         📍 Location: {appointment.location or 'Our Medical Center'}

#         Please arrive 15 minutes early for your appointment. If you need to reschedule or cancel, please contact us at least 24 hours in advance.

#         We look forward to seeing you!

#         Best regards,
#         Dr. {self.provider.last_name}'s Office
#         """
#         msg_service = MessageService(self.provider)
#         msg_service.send_message(appointment.patient, msg)

#         return appointment

# class AdminAppointmentService:
#     def __init__(self, admin_staff: AdminStaff):
#         self.admin_staff = admin_staff

#     # TODO: view all provider working in admin staff's hospital's appointments

#     def manage_appointment(self, appointment: Appointment,
#                            action: str, **kwargs) -> Appointment:
#         # Check if appointment is with healthcare provider the admin staff
#         # manages.
#         admin_hospital = self.admin_staff.admin_staff_profile.hospital # type: ignore
#         healthcare_provider = appointment.healthcare_provider

#         is_affiliated = False
#         if healthcare_provider and healthcare_provider.healthcare_provider_profile: # type: ignore
#             profile = healthcare_provider.healthcare_provider_profile # type: ignore

#             if profile.hospitals.filter(id=admin_hospital.id).exists():
#                 is_affiliated = True
#             elif profile.primary_hospital and profile.primary_hospital.id == admin_hospital.id:
#                 is_affiliated = True

#         if not is_affiliated:
#             raise PermissionError("Cannot manage appointments from another hospital.")

#         if action == 'reschedule':
#             new_start_datetime = kwargs.get('new_start_datetime')
#             new_end_datetime = kwargs.get('new_end_datetime')

#             if new_start_datetime is None or new_end_datetime is None:
#                 raise ValueError("new_start_datetime and new_end_datetime parameter is required for rescheduling.")
#             if not isinstance(new_start_datetime, datetime) or not isinstance(new_end_datetime, datetime):
#                 raise TypeError("new_date must be a datetime object.")
#             if new_end_datetime < new_start_datetime:
#                 raise ValueError("End time must be greater than start time")

#             appointment.appointment_start_datetime_utc = new_start_datetime
#             appointment.appointment_end_datetime_utc = new_end_datetime
#             appointment.status = Appointment.Status.RESCHEDULED
#         elif action == 'cancel':
#             appointment.status = Appointment.Status.CANCELLED
#         elif action == 'complete':
#             appointment.status = Appointment.Status.COMPLETED
#         else:
#             raise ValueError("Unknown action.")

#         appointment.save()
#         return appointment

# class MedicalRecordService:
#     @staticmethod
#     def view_medical_records(patient: Patient, date_range: Optional[List[datetime]]=None,
#                              provider:Optional['HealthcareProvider']=None,
#                              limit: Optional[int]=None) -> QuerySet:
#         queryset = patient.medical_records.all() # type: ignore

#         if date_range: # [start_date, end_date]
#             queryset = queryset.filter(record_date__range=date_range)

#         if provider:
#             queryset = queryset.filter(healthcare_provider=provider)

#         if limit:
#             queryset = queryset[:limit]

#         return queryset

#     @staticmethod
#     def add_medical_record(patient: Patient, provider: HealthcareProvider,
#                            diagnosis: str, notes: str,
#                            prescriptions: str) -> MedicalRecord:
#         if not diagnosis.strip():
#             raise ValueError("Cannot have empty diagnosis")
#         if not notes.strip():
#             raise ValueError("Cannot have empty notes")
#         if not prescriptions.strip():
#             raise ValueError("Cannot have empty prescriptions")

#         medical_record = MedicalRecord(
#             patient=patient,
#             healthcare_provider=provider,
#             diagnosis=diagnosis,
#             notes=notes,
#             prescriptions=prescriptions
#         )
#         medical_record.save()
#         return medical_record

# class AvailabilityService:
#     def __init__(self, provider: HealthcareProvider):
#         self.provider = provider

#     def _validate_day(self, day: str):
#         valid_days = [choice[0] for choice in Availability.DaysOfWeek.choices]
#         if day not in valid_days:
#             raise ValueError(f"Invalid day of week: {day}. Must be one of {valid_days}")

#     def _validate_time(self, start_time: datetime, end_time: datetime):
#         if start_time >= end_time:
#             raise ValueError("Start time must be before end time")

#     def set_availability(self, slots: Dict[Availability.DaysOfWeek, tuple[datetime, ...]]) -> List['Availability']:
#         # validate time slots
#         for day, (start_time, end_time) in slots.items():
#             self._validate_day(day)
#             self._validate_time(start_time, end_time)

#         for day, (start_time, end_time) in slots.items():
#             Availability.objects.update_or_create(
#                 healthcare_provider=self.provider,
#                 day_of_week=day,
#                 start_time=start_time,
#                 end_time=end_time
#             )

#         valid_days = {choice[0] for choice in Availability.DaysOfWeek.choices}
#         remaining_days = valid_days - set(slots.keys())
#         self.remove_availability(list(remaining_days))

#         return self.provider.availability_slots.all() # type: ignore

#     def remove_availability(self, days_of_week: List[str]) -> int:
#         for day in days_of_week:
#             self._validate_day(day)

#         count, _ = self.provider.availability_slots.filter(day_of_week__in=days_of_week).delete() # type: ignore
#         return count

# class TimeOffService:
#     def __init__(self, provider: HealthcareProvider):
#         self.provider = provider

#     def set_timeoff(self, start_datetime_utc: datetime, end_datetime_utc: datetime) -> TimeOff:
#         now = timezone.now()

#         if end_datetime_utc < now:
#             raise ValueError("Cannot set time off for a past time")

#         if start_datetime_utc >= end_datetime_utc:
#             raise ValueError("Start time must be before end datetime")

#         return TimeOff.objects.create(
#             healthcare_provider=self.provider,
#             start_datetime_utc=start_datetime_utc,
#             end_datetime_utc=end_datetime_utc
#         )

#     def view_timeoff(self, upcoming: Optional[bool] = None) -> QuerySet:
#         now = timezone.now()
#         queryset = self.provider.provider_timeoff.all() # type: ignore

#         if upcoming is True:
#             return queryset.filter(start_datetime_utc__gt=now)
#         elif upcoming is False:
#             return queryset.filter(start_datetime_utc__lt=now)
#         else:
#             return queryset
