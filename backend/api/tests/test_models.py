# type: ignore
import os
import time
from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from ..models import (
    User, Patient, HealthcareProvider, AdminStaff, SystemAdmin,
    Speciality, Hospital, PatientProfile, HealthcareProviderProfile,
    AdminStaffProfile, SystemAdminProfile, Appointment, MedicalRecord,
    Message, ProviderHospitalAssignment, Slot
)

User = get_user_model()

class BaseModelTest(TestCase):
    def setUp(self):
        self.speciality = Speciality.objects.create(
            name='Gynecologist',
            image='Gynecologist.svg'
        )
        
        self.hospital = Hospital.objects.create(
            name="General Hospital",
            address="123 Main St",
            phone_number="123-456-7890"
        )
        
        self.hospital2 = Hospital.objects.create(
            name="Veteran Hospital",
            address="123 Valley Ave",
            phone_number="123-456-7890"
        )
        
class UserModelTest(BaseModelTest):
    def test_create_user(self):
        user = User.objects.create_user(
            username="test",
            password="password1234",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        
        self.assertEqual(user.username, "test")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.type, User.UserType.PATIENT) 
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        
    def test_create_superuser(self):
        user = User.objects.create_superuser(
            username="admin",
            password="password1234",
            email="admin@example.com",
            first_name="Admin",
            last_name="User"
        )
        
        self.assertEqual(user.username, "admin")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        
    def test_create_patient_proxy(self):
        user = User.objects.create_user(
            username="test",
            password="password1234",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        
        patient_profile = PatientProfile.objects.create(
            user=user,
            age=24,
            blood_type="O",
            allergies="peanut",
            insurance="Blue Cross",
            weight=70,
            height=175
        )
        
        patient = Patient.objects.get(id=user.id) 
        self.assertEqual(patient.type, User.UserType.PATIENT) 
        self.assertEqual(patient.profile, patient_profile)
        
    def test_create_healthcare_provider_proxy(self):
        user = User.objects.create_user(
            username="doc",
            password="password1234",
            email="doc@example.com",
            type=User.UserType.HEALTHCARE_PROVIDER, 
            first_name="Doc",
            last_name="User"
        )
        provider_profile = HealthcareProviderProfile.objects.create(
            user=user,
            speciality=self.speciality,
            image="doctor.jpg",
            education="MD",
            years_of_experience=10,
            about="Experienced professional",
            fees=150.,
            address_line1="123 Main St",
            city="Los Angeles",
            state="CA",
            zip_code="90012",
            license_number="G40749",
            primary_hospital=self.hospital
        )
        
        provider = HealthcareProvider.objects.get(id=user.id) 
        self.assertEqual(provider.type, User.UserType.HEALTHCARE_PROVIDER) 
        self.assertEqual(provider.profile, provider_profile)
        self.assertEqual(provider_profile.fees, 150.)
        
    def test_create_admin_staff_proxy(self):
        user = User.objects.create_user(
            username="admin",
            password="password1234",
            email="admin@example.com",
            type=User.UserType.ADMIN_STAFF, 
            first_name="Admin",
            last_name="User"
        )
        admin_staff_profile = AdminStaffProfile.objects.create(
            user=user,
            hospital=self.hospital
        )
        admin_staff = AdminStaff.objects.get(id=user.id) 
        
        self.assertEqual(user.type, User.UserType.ADMIN_STAFF) 
        self.assertEqual(admin_staff.admin_staff_profile, admin_staff_profile) 
        
    def test_create_system_admin_proxy(self):
        user = User.objects.create_user(
            username="sysadmin",
            password="password1234",
            email="sysadmin@example.com",
            type=User.UserType.SYSTEM_ADMIN, 
        )
        sys_admin_profile = SystemAdminProfile.objects.create(
            user=user
        )
        sysadmin = SystemAdmin.objects.get(id=user.id) 
        
        self.assertEqual(user.type, User.UserType.SYSTEM_ADMIN) 
        self.assertEqual(sysadmin.system_admin_profile, sys_admin_profile)
        
#     def test_send_message(self):
#         patient_user = User.objects.create_user(
#             username="test",
#             password="password1234",
#             email="test@example.com",
#             type=User.UserType.PATIENT, 
#             first_name="Test",
#             last_name="User"
#         )
#         provider_user = User.objects.create_user(
#             username="doc",
#             password="password1234",
#             email="doc@example.com",
#             type=User.UserType.HEALTHCARE_PROVIDER, 
#             first_name="Doc",
#             last_name="User"
#         )
        
#         message = patient_user.send_message(provider_user, "test") 
#         self.assertEqual(message.sender, patient_user)
#         self.assertEqual(message.recipient, provider_user)
#         self.assertEqual(message.content, 'test')
#         self.assertFalse(message.read)
        
#     def test_send_invalid_message(self):
#         patient_user = User.objects.create_user(
#             username="test",
#             password="password1234",
#             email="test@example.com",
#             type=User.UserType.PATIENT, 
#             first_name="Test",
#             last_name="User"
#         )
#         provider_user = User.objects.create_user(
#             username="doc",
#             password="password1234",
#             email="doc@example.com",
#             type=User.UserType.HEALTHCARE_PROVIDER, 
#             first_name="Doc",
#             last_name="User"
#         )
        
#         with self.assertRaises(ValueError):
#             patient_user.send_message(recipient=provider_user, content="") 
            
#     def test_view_message(self):
#         patient_user = User.objects.create_user(
#             username="test",
#             password="password1234",
#             email="test@example.com",
#             type=User.UserType.PATIENT, 
#             first_name="Test",
#             last_name="User"
#         )
#         provider_user = User.objects.create_user(
#             username="doc",
#             password="password1234",
#             email="doc@example.com",
#             type=User.UserType.HEALTHCARE_PROVIDER, 
#             first_name="Doc",
#             last_name="User"
#         )
        
#         message = patient_user.send_message(provider_user, "test") 
#         received_messages = provider_user.view_message(patient_user) 
#         self.assertEqual(len(received_messages), 1)
#         self.assertEqual(received_messages[0], message)
#         self.assertEqual(received_messages[0].sender, patient_user) 
        
#     def test_get_conversation(self):
#         patient_user = User.objects.create_user(
#             username="test",
#             password="password1234",
#             email="test@example.com",
#             type=User.UserType.PATIENT, 
#             first_name="Test",
#             last_name="User"
#         )
#         provider_user = User.objects.create_user(
#             username="doc",
#             password="password1234",
#             email="doc@example.com",
#             type=User.UserType.HEALTHCARE_PROVIDER, 
#             first_name="Doc",
#             last_name="User"
#         )
#         provider_user2 = User.objects.create_user(
#             username="doc2",
#             password="password1234",
#             email="doc2@example.com",
#             type=User.UserType.HEALTHCARE_PROVIDER, 
#             first_name="Doc2",
#             last_name="User"
#         )
        
#         patient_user.send_message(provider_user, "test")
#         self.assertEqual(len(patient_user.get_conversation(provider_user)), 1) 
#         self.assertEqual(len(patient_user.get_conversation(provider_user2)), 0) 
        
#     def test_get_unread_count(self):
#         patient_user = User.objects.create_user(
#             username="test",
#             password="password1234",
#             email="test@example.com",
#             type=User.UserType.PATIENT, 
#             first_name="Test",
#             last_name="User"
#         )
#         provider_user = User.objects.create_user(
#             username="doc",
#             password="password1234",
#             email="doc@example.com",
#             type=User.UserType.HEALTHCARE_PROVIDER, 
#             first_name="Doc",
#             last_name="User"
#         )
#         provider_user2 = User.objects.create_user(
#             username="doc2",
#             password="password1234",
#             email="doc@example.com",
#             type=User.UserType.HEALTHCARE_PROVIDER,
#             first_name="Doc2",
#             last_name="User"
#         )
        
#         provider_user.send_message(patient_user, "test")
#         provider_user2.send_message(patient_user, "test") 
#         self.assertEqual(patient_user.get_unread_count(), 2) 
#         self.assertEqual(provider_user.get_unread_count(), 0)
        
#     def test_mark_as_read(self):
#         patient_user = User.objects.create_user(
#             username="test",
#             password="password1234",
#             email="test@example.com",
#             type=User.UserType.PATIENT, 
#             first_name="Test",
#             last_name="User"
#         )
#         provider_user = User.objects.create_user(
#             username="doc",
#             password="password1234",
#             email="doc@example.com",
#             type=User.UserType.HEALTHCARE_PROVIDER, 
#             first_name="Doc",
#             last_name="User"
#         )
#         provider_user.send_message(patient_user, "test")
#         patient_user.mark_as_read(other_user=provider_user)

#         self.assertEqual(patient_user.get_unread_count(), 0)
#         self.assertTrue(patient_user.view_message(provider_user)[0].read)
        
#         message = patient_user.send_message(provider_user, "test2")
#         provider_user.mark_as_read([message])

#         self.assertEqual(provider_user.get_unread_count(), 0)
#         self.assertTrue(provider_user.view_message(provider_user)[0].read)
        
#     def test_invalid_mark_as_read(self):
#         patient_user = User.objects.create_user(
#             username="test",
#             password="password1234",
#             email="test@example.com",
#             type=User.UserType.PATIENT, 
#             first_name="Test",
#             last_name="User"
#         )
#         provider_user = User.objects.create_user(
#             username="doc",
#             password="password1234",
#             email="doc@example.com",
#             type=User.UserType.HEALTHCARE_PROVIDER, 
#             first_name="Doc",
#             last_name="User"
#         )
#         provider_user2 = User.objects.create_user(
#             username="doc2",
#             password="password1234",
#             email="doc2@example.com",
#             type=User.UserType.HEALTHCARE_PROVIDER, 
#             first_name="Doc2",
#             last_name="User"
#         )
#         message = provider_user.send_message(patient_user, "test")
        
#         with self.assertRaises(PermissionError):
#             provider_user2.mark_as_read([message]) 
#         with self.assertRaises(PermissionError):
#             provider_user.mark_as_read([message])
            
#         provider_user.mark_as_read(other_user=patient_user)
#         self.assertEqual(patient_user.get_unread_count(), 1)
#         self.assertFalse(patient_user.view_message(provider_user)[0].read)

# class PatientModelTest(BaseModelTest):
#     def setUp(self):
#         super().setUp()
        
#         self.patient_user = User.objects.create_user(
#             username="test",
#             password="password1234",
#             email="test@example.com",
#             type=User.UserType.PATIENT, 
#             first_name="Test",
#             last_name="User"
#         )
        
#         self.patient_profile = PatientProfile.objects.create(
#             user=self.patient_user,
#             age=25,
#             blood_type="A+"
#         )
        
#         self.patient = Patient.objects.get(id=self.patient_user.id) 
#         self.provider_user = User.objects.create_user(
#             username="doc",
#             password="password1234",
#             email="doc@example.com",
#             type=User.UserType.HEALTHCARE_PROVIDER, 
#             first_name="Doc",
#             last_name="User"
#         )
        
#         self.provider_profile = HealthcareProviderProfile.objects.create(
#             user=self.provider_user,
#             speciality=self.speciality,
#             image="doctor.jpg",
#             education="MD",
#             years_of_experience=5,
#             about="Test doctor",
#             fees=100.,
#             address_line1="123 Test St",
#             city="Test City",
#             state="TS",
#             zip_code="12345",
#             license_number="MD654321",
#             primary_hospital=self.hospital
#         )
        
#         self.provider = HealthcareProvider.objects.get(id=self.provider_user.id) 
        
#     def test_patient_view_doctors(self):
#         doctors = self.patient.view_healthcare_providers() 
#         self.assertEqual(doctors.count(), 1)
#         self.assertEqual(doctors.first(), self.provider)
        
#     def test_patient_search_doctors(self):
#         """Test patient can search doctors by speciality"""
#         # Search with matching speciality
#         doctors = self.patient.search_healthcare_providers(speciality=self.speciality.name) 
#         self.assertEqual(doctors.count(), 1)
        
#         # Search with non-matching speciality
#         doctors = self.patient.search_healthcare_providers(speciality="Dermatology") 
#         self.assertEqual(doctors.count(), 0)
        
#         # Search without speciality
#         doctors = self.patient.search_healthcare_providers()
#         self.assertEqual(doctors.count(), 1)
        
#     def test_patient_schedule_appointment(self):
#         start_time = timezone.now() + timedelta(days=1)
#         end_time = timezone.now() + timedelta(days=2)
        
#         appointment = self.patient.schedule_appointment(
#             healthcare_providers=self.provider,
#             start_datetime_utc=start_time,
#             end_datetime_utc=end_time,
#             reason="Test"
#         )
        
#         self.assertEqual(appointment.patient, self.patient)
#         self.assertEqual(appointment.healthcare_provider, self.provider)
#         self.assertEqual(appointment.status, Appointment.Status.REQUESTED)
#         self.assertEqual(appointment.reason, "Test")

#     def test_patient_schedule_past_appointment(self):
#         start_time = timezone.now() - timedelta(days=1)
#         end_time = timezone.now() + timedelta(days=1)
        
#         with self.assertRaises(ValidationError):
#             self.patient.schedule_appointment(
#                 healthcare_providers=self.provider,
#                 start_datetime_utc=start_time,
#                 end_datetime_utc=end_time,
#                 reason="Test"
#             )
            
#     def test_patient_schedule_start_time_after_end_time(self):
#         start_time = timezone.now() - timedelta(days=1)
#         end_time = timezone.now() - timedelta(days=2)
        
#         with self.assertRaises(ValueError):
#             self.patient.schedule_appointment(
#                 healthcare_providers=self.provider,
#                 start_datetime_utc=start_time,
#                 end_datetime_utc=end_time,
#                 reason="Test"
#             )

#     def test_view_patient_appointments(self):
#         past_appt = Appointment.objects.create(
#             patient=self.patient,
#             healthcare_provider=self.provider,
#             appointment_start_datetime_utc=timezone.now() + timedelta(seconds=1),
#             appointment_end_datetime_utc=timezone.now() + timedelta(seconds=2),
#             location="Test",
#             reason="Past appointment",
#             status=Appointment.Status.COMPLETED
#         )
#         time.sleep(2)
        
#         future_appt = Appointment.objects.create(
#             patient=self.patient,
#             healthcare_provider=self.provider,
#             appointment_start_datetime_utc=timezone.now() + timedelta(days=2),
#             appointment_end_datetime_utc=timezone.now() + timedelta(days=4),
#             location="Test",
#             reason="Future appointment",
#             status=Appointment.Status.CONFIRMED
#         )

#         past = self.patient.view_appointments(upcoming=False)
#         self.assertEqual(past.count(), 1)
#         self.assertEqual(past.first(), past_appt)

#         upcoming = self.patient.view_appointments(upcoming=True)
#         self.assertEqual(upcoming.count(), 1)
#         self.assertEqual(upcoming.first(), future_appt)
        
#         confirmed = self.patient.view_appointments(status=Appointment.Status.CONFIRMED)
#         self.assertEqual(confirmed.count(), 1)
        
#         statuses = [Appointment.Status.CONFIRMED, Appointment.Status.COMPLETED]
#         multiple_status = self.patient.view_appointments(status=statuses)
#         self.assertEqual(multiple_status.count(), 2)

# class HealthcareProviderModelTest(BaseModelTest):
#     def setUp(self):
#         super().setUp()
        
#         self.patient_user = User.objects.create_user(
#             username="test",
#             password="password1234",
#             email="test@example.com",
#             type=User.UserType.PATIENT, 
#             first_name="Test",
#             last_name="User"
#         )
        
#         self.patient_profile = PatientProfile.objects.create(
#             user=self.patient_user,
#             age=25,
#             blood_type="A+"
#         )
        
#         self.patient = Patient.objects.get(id=self.patient_user.id) 
        
#         # Create healthcare provider
#         self.provider_user = User.objects.create_user(
#             username="doc",
#             password="password1234",
#             email="doc@example.com",
#             type=User.UserType.HEALTHCARE_PROVIDER, 
#             first_name="Doc",
#             last_name="User"
#         )
        
#         self.provider_profile = HealthcareProviderProfile.objects.create(
#             user=self.provider_user,
#             speciality=self.speciality,
#             image="doctor.jpg",
#             education="MD",
#             years_of_experience=5,
#             about="Test doctor",
#             fees=100.,
#             address_line1="123 Test St",
#             city="Test City",
#             state="TS",
#             zip_code="12345",
#             license_number="MD654321",
#             primary_hospital=self.hospital
#         )
        
#         self.provider_user2 = User.objects.create_user(
#             username="doc2",
#             password="password1234",
#             email="doc2@example.com",
#             type=User.UserType.HEALTHCARE_PROVIDER, 
#             first_name="Doc2",
#             last_name="User"
#         )
        
#         self.provider = HealthcareProvider.objects.get(id=self.provider_user.id) 
#         self.provider2 = HealthcareProvider.objects.get(id=self.provider_user2.id) 
        
#     # def test_provider_set_availability(self):
#     #     start_time = datetime.strptime("09:00", "%H:%M")
#     #     end_time = datetime.strptime("17:00", "%H:%M")
        
#     #     self.provider.set_availability({
#     #         "MON": (start_time, end_time),
#     #         "TUE": (start_time, end_time),
#     #         "WED": (start_time, end_time),
#     #         "THU": (start_time, end_time),
#     #         "FRI": (start_time, end_time)
#     #     })
#     #     availabilities = Availability.objects.filter(healthcare_provider=self.provider)
#     #     self.assertEqual(availabilities.count(), 5)
        
#     #     # Update availability
#     #     self.provider.set_availability({
#     #         "MON": (start_time, end_time)
#     #     })
#     #     availabilities = Availability.objects.filter(healthcare_provider=self.provider)
#     #     self.assertEqual(availabilities.count(), 1)
        
#     # def test_provider_remove_availability(self):
#     #     start_time = datetime.strptime("09:00", "%H:%M")
#     #     end_time = datetime.strptime("17:00", "%H:%M")
        
#     #     self.provider.set_availability({
#     #         "MON": (start_time, end_time)
#     #     })
#     #     availabilities = Availability.objects.filter(healthcare_provider=self.provider)
#     #     self.assertEqual(availabilities.count(), 1)

#     #     self.provider.remove_availability(["MON"])
#     #     availabilities = Availability.objects.filter(healthcare_provider=self.provider)
#     #     self.assertEqual(availabilities.count(), 0)
        
#     # def test_invalid_day(self):
#     #     start_time = datetime.strptime("09:00", "%H:%M")
#     #     end_time = datetime.strptime("17:00", "%H:%M")
        
#     #     with self.assertRaises(ValueError):
#     #         self.provider.set_availability({
#     #             "SUNDAY": (start_time, end_time)
#     #         })
            
#     # def test_invalid_time(self):
#     #     start_time = datetime.strptime("17:00", "%H:%M")
#     #     end_time = datetime.strptime("09:00", "%H:%M")
        
#     #     with self.assertRaises(ValueError):
#     #         self.provider.set_availability({
#     #             "MON": (start_time, end_time)
#     #         })
            
#     # def test_provider_set_timeoff(self):
#     #     start_time = timezone.now() + timedelta(days=1)
#     #     end_time = timezone.now() + timedelta(days=2)
        
#     #     self.provider.set_timeoff(start_time, end_time)
        
#     #     timeoffs = self.provider.view_timeoff()
#     #     self.assertEqual(len(timeoffs), 1)
#     #     self.assertEqual(timeoffs[0].start_datetime_utc, start_time)
#     #     self.assertEqual(timeoffs[0].end_datetime_utc, end_time)
    
#     def test_view_appointment_schedule(self):
#         start_time = timezone.now() + timedelta(days=1)
#         end_time = timezone.now() + timedelta(days=2)
        
#         appointment = self.patient.schedule_appointment(
#             healthcare_providers=self.provider,
#             start_datetime_utc=start_time,
#             end_datetime_utc=end_time,
#             reason="Test"
#         )
#         provider_appointments = self.provider.view_appointment_schedule("month")
        
#         self.assertEqual(provider_appointments.count(), 1)
#         self.assertEqual(self.provider2.view_appointment_schedule("month").count(), 0)
#         self.assertEqual(provider_appointments[0], appointment)
#         self.assertEqual(provider_appointments[0].status, Appointment.Status.REQUESTED)
        
#     def test_accept_appointment(self):
#         start_time = timezone.now() + timedelta(days=1)
#         end_time = timezone.now() + timedelta(days=2)
        
#         appointment = self.patient.schedule_appointment(
#             healthcare_providers=self.provider,
#             start_datetime_utc=start_time,
#             end_datetime_utc=end_time,
#             reason="Test"
#         )

#         self.provider.accept_appointment(appointment)
#         self.assertEqual(self.provider.view_appointment_schedule("month").first().status,
#                          Appointment.Status.CONFIRMED)
#         self.assertEqual(self.patient.get_unread_count(), 1)
        
#     def test_invalid_accept_appointment(self):
#         start_time = timezone.now() + timedelta(days=1)
#         end_time = timezone.now() + timedelta(days=2)
        
#         appointment = self.patient.schedule_appointment(
#             healthcare_providers=self.provider,
#             start_datetime_utc=start_time,
#             end_datetime_utc=end_time,
#             reason="Test"
#         )

#         with self.assertRaises(PermissionError):
#             self.provider2.accept_appointment(appointment)
            
#         self.provider.accept_appointment(appointment)
#         with self.assertRaises(ValueError):
#             self.provider.accept_appointment(appointment)
            
#     def test_add_medical_record(self):
#         med_record = self.provider.add_medical_record(
#             patient=self.patient,
#             diagnosis="test",
#             notes="test",
#             prescriptions="test"
#         )

#         self.assertEqual(self.patient.view_medical_records()[0], med_record)
        
#     def test_invalid_add_medical_record(self):
#         with self.assertRaises(ValueError):
#             self.provider.add_medical_record(
#                 patient=self.patient,
#                 diagnosis="",
#                 notes="test",
#                 prescriptions="test"
#             )
#         with self.assertRaises(ValueError):
#             self.provider.add_medical_record(
#                 patient=self.patient,
#                 diagnosis="test",
#                 notes="",
#                 prescriptions="test"
#             )
#         with self.assertRaises(ValueError):
#             self.provider.add_medical_record(
#                 patient=self.patient,
#                 diagnosis="test",
#                 notes="test",
#                 prescriptions=""
#             )
            
# class AdminStaffModelTest(BaseModelTest):
#     def setUp(self):
#         super().setUp()
        
#         self.patient_user = User.objects.create_user(
#             username="test",
#             password="password1234",
#             email="test@example.com",
#             type=User.UserType.PATIENT, 
#             first_name="Test",
#             last_name="User"
#         )
#         self.patient_profile = PatientProfile.objects.create(
#             user=self.patient_user,
#             age=25,
#             blood_type="A+"
#         )
#         self.patient = Patient.objects.get(id=self.patient_user.id) 
        
#         self.provider_user = User.objects.create_user(
#             username="doc",
#             password="password1234",
#             email="doc@example.com",
#             type=User.UserType.HEALTHCARE_PROVIDER, 
#             first_name="Doc",
#             last_name="User"
#         )
        
#         self.provider_profile = HealthcareProviderProfile.objects.create(
#             user=self.provider_user,
#             speciality=self.speciality,
#             image="doctor.jpg",
#             education="MD",
#             years_of_experience=5,
#             about="Test doctor",
#             fees=100.,
#             address_line1="123 Test St",
#             city="Test City",
#             state="TS",
#             zip_code="12345",
#             license_number="MD654321",
#             primary_hospital=self.hospital
#         )
#         self.provider = HealthcareProvider.objects.get(id=self.provider_user.id)
        
#         start_time = timezone.now() + timedelta(days=1)
#         end_time = timezone.now() + timedelta(days=2)
#         self.appointment = self.patient.schedule_appointment(
#             healthcare_providers=self.provider,
#             start_datetime_utc=start_time,
#             end_datetime_utc=end_time,
#             reason="Test"
#         )
        
#         self.admin_staff_user = User.objects.create(
#             username="admin",
#             password="password1234",
#             email="admin@example.com",
#             type=User.UserType.ADMIN_STAFF, 
#             first_name="Admin",
#             last_name="User"
#         )
#         self.admin_staff_profile = AdminStaffProfile.objects.create(
#             user=self.admin_staff_user,
#             hospital=self.hospital
#         )
#         self.admin_staff = AdminStaff.objects.get(id=self.admin_staff_user.id)
    
#     def test_manage_appointment(self):
#         start_time = timezone.now() + timedelta(days=7)
#         end_time = timezone.now() + timedelta(days=8)
        
#         self.admin_staff.manage_appointment(self.appointment,
#                                             action="reschedule",
#                                             new_start_datetime=start_time,
#                                             new_end_datetime=end_time)
        
#         self.assertEqual(self.patient.view_appointments(status=Appointment.Status.RESCHEDULED).count(), 1)
        
#         self.admin_staff.manage_appointment(self.appointment,
#                                             action="cancel")
#         self.assertEqual(self.patient.view_appointments(status=Appointment.Status.CANCELLED).count(), 1)
        
#         self.admin_staff.manage_appointment(self.appointment,
#                                             action="complete")
#         self.assertEqual(self.patient.view_appointments(status=Appointment.Status.COMPLETED).count(), 1)
        
#     def test_invalid_manage_appointment(self):
#         start_time = timezone.now() + timedelta(days=7)
#         end_time = timezone.now() + timedelta(days=8)
        
#         with self.assertRaises(ValueError):
#             self.admin_staff.manage_appointment(self.appointment,
#                                     action="reschedule",
#                                     new_start_datetime=None,
#                                     new_end_datetime=end_time)
#         with self.assertRaises(ValueError):
#             self.admin_staff.manage_appointment(self.appointment,
#                                     action="reschedule",
#                                     new_start_datetime=start_time,
#                                     new_end_datetime=None)
#         with self.assertRaises(ValueError):
#             self.admin_staff.manage_appointment(self.appointment,
#                                     action="reschedule",
#                                     new_start_datetime=end_time,
#                                     new_end_datetime=start_time)
        
#         self.admin_staff_profile.hospital = self.hospital2
#         self.admin_staff_profile.save()
#         self.admin_staff.refresh_from_db()
#         with self.assertRaises(PermissionError):
#             self.admin_staff.manage_appointment(self.appointment,
#                                     action="reschedule",
#                                     new_start_datetime=start_time,
#                                     new_end_datetime=end_time)
            
# class SystemAdminModelTest(BaseModelTest):
#     def setUp(self):
#         super().setUp()
        
#         self.patient_user = User.objects.create_user(
#             username="test",
#             password="password1234",
#             email="test@example.com",
#             type=User.UserType.PATIENT, 
#             first_name="Test",
#             last_name="User"
#         )
#         self.patient_profile = PatientProfile.objects.create(
#             user=self.patient_user,
#             age=25,
#             blood_type="A+"
#         )
#         self.patient = Patient.objects.get(id=self.patient_user.id) 
        
#         self.provider_user = User.objects.create_user(
#             username="doc",
#             password="password1234",
#             email="doc@example.com",
#             type=User.UserType.HEALTHCARE_PROVIDER, 
#             first_name="Doc",
#             last_name="User"
#         )
        
#         self.provider_profile = HealthcareProviderProfile.objects.create(
#             user=self.provider_user,
#             speciality=self.speciality,
#             image="doctor.jpg",
#             education="MD",
#             years_of_experience=5,
#             about="Test doctor",
#             fees=100.,
#             address_line1="123 Test St",
#             city="Test City",
#             state="TS",
#             zip_code="12345",
#             license_number="MD654321",
#             primary_hospital=self.hospital
#         )
        
#         self.provider = HealthcareProvider.objects.get(id=self.provider_user.id)
        
#         self.sys_admin_user = User.objects.create(
#             username="sysadmin",
#             password="password1234",
#             email="sysadmin@example.com",
#             type=User.UserType.SYSTEM_ADMIN, 
#             first_name="Sysadmin",
#             last_name="User"
#         )
#         self.sys_admin_profile = SystemAdminProfile.objects.create(
#             user=self.sys_admin_user
#         )
#         self.admin_staff = SystemAdmin.objects.get(id=self.sys_admin_user.id)

#     def test_create_user_account(self):
#         patient, patient_profile = self.admin_staff.create_user_account(
#             username="bob",
#             password="password1234",
#             email="bob@example.com",
#             type=User.UserType.PATIENT, 
#             first_name="Bob",
#             last_name="User",
#             age=25
#         )
        
#         self.assertEqual(patient.username, 'bob')
#         self.assertEqual(patient.email, "bob@example.com")
#         self.assertEqual(patient.type, User.UserType.PATIENT)
#         self.assertEqual(patient.first_name, "Bob")
#         self.assertEqual(patient.last_name, "User")
#         self.assertEqual(patient.patient_profile, patient_profile)
        
#         provider, provider_profile = self.admin_staff.create_user_account(
#             username="test2",
#             password="password1234",
#             email="test2@example.com",
#             speciality=self.speciality,
#             image="doctor.jpg",
#             education="MD",
#             years_of_experience=5,
#             about="Test doctor",
#             fees=100.,
#             address_line1="123 Test St",
#             city="Test City",
#             state="TS",
#             zip_code="12345",
#             license_number="MD654321",
#             primary_hospital=self.hospital,
#             type=User.UserType.HEALTHCARE_PROVIDER,
#             first_name="Test2",
#             last_name="User",
#         )
        
#         self.assertEqual(provider_profile.years_of_experience, 5)
#         self.assertEqual(provider_profile.about, "Test doctor")
#         self.assertEqual(provider_profile.license_number, "MD654321")
#         self.assertEqual(provider_profile.primary_hospital, self.hospital)
#         self.assertEqual(provider.type, User.UserType.HEALTHCARE_PROVIDER)
#         self.assertEqual(provider.healthcare_provider_profile, provider_profile)
        
#         admin_staff, admin_staff_profile = self.admin_staff.create_user_account(
#             username="test3",
#             password="password1234",
#             email="test3@example.com",
#             type=User.UserType.ADMIN_STAFF, 
#             first_name="Test",
#             last_name="User",
#             hospital=self.hospital
#         )
        
#         self.assertEqual(admin_staff.type, User.UserType.ADMIN_STAFF)
#         self.assertEqual(admin_staff_profile.hospital, self.hospital)
#         self.assertEqual(admin_staff.admin_staff_profile, admin_staff_profile)
        
#     def test_invalid_create_user_account(self):
#         with self.assertRaises(IntegrityError):
#             self.admin_staff.create_user_account(
#                 username="bob",
#                 password="password1234",
#                 email="bob@example.com",
#                 type=User.UserType.PATIENT,
#                 first_name="Bob",
#                 last_name="User"
#             )
            
#         with self.assertRaises(ValidationError):
#             self.admin_staff.create_user_account(
#                 username="bob",
#                 password="password1234",
#                 email="bob@example.com",
#                 type="others",
#                 first_name="Bob",
#                 last_name="User",
#                 age=10
#             )
            
#         with self.assertRaises(ValidationError):
#             self.admin_staff.create_user_account(
#                 username="bob",
#                 password="password1234",
#                 email="bob@example.com",
#                 fees=100.,
#                 address_line1="123 Test St",
#                 city="Test City",
#                 state="TS",
#                 zip_code="12345",
#                 license_number="MD654321",
#                 primary_hospital=self.hospital,
#                 type=User.UserType.HEALTHCARE_PROVIDER,
#                 first_name="Bob",
#                 last_name="User",
#             )
            
#         with self.assertRaises(ValidationError):
#             self.admin_staff.create_user_account(
#                 username="bob",
#                 password="password1234",
#                 email="bob@example.com",
#                 type=User.UserType.ADMIN_STAFF, 
#                 first_name="Bob",
#                 last_name="User",
#             )
