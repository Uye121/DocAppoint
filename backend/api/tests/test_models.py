import os
from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError

from ..models import (
    User, Patient, HealthcareProvider, AdminStaff, SystemAdmin,
    Speciality, Hospital, PatientProfile, HealthcareProviderProfile,
    AdminStaffProfile, Appointment, MedicalRecord, Message,
    Availability, TimeOff, ProviderHospitalAssignment
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
        
        self.hospital = Hospital.objects.create(
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
        self.assertEqual(user.type, User.UserType.PATIENT) # type: ignore
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
        
        patient = Patient.objects.get(id=user.id) # type: ignore
        self.assertEqual(patient.type, User.UserType.PATIENT) # type: ignore
        self.assertEqual(patient.profile, patient_profile)
        
    def test_create_healthcare_provider_proxy(self):
        user = User.objects.create_user(
            username="doc",
            password="password1234",
            email="doc@example.com",
            type=User.UserType.HEALTHCARE_PROVIDER, # type: ignore
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
        
        provider = HealthcareProvider.objects.get(id=user.id) # type: ignore
        self.assertEqual(provider.type, User.UserType.HEALTHCARE_PROVIDER) # type: ignore
        self.assertEqual(provider.profile, provider_profile)
        
    def test_create_admin_staff_proxy(self):
        user = User.objects.create_user(
            username="admin",
            password="password1234",
            email="admin@example.com",
            type=User.UserType.ADMIN_STAFF, # type: ignore
            first_name="Admin",
            last_name="User"
        )
        admin_profile = AdminStaffProfile.objects.create(
            user=user,
            hospital=self.hospital
        )
        
        admin = AdminStaff.objects.get(id=user.id) # type: ignore
        self.assertEqual(admin.type, User.UserType.ADMIN_STAFF) # type: ignore
        self.assertEqual(admin.admin_staff_profile, admin_profile) # type: ignore
        
    def test_create_system_admin_proxy(self):
        sysadmin_user = User.objects.create_user(
            username="sysadmin",
            password="password1234",
            email="sysadmin@example.com",
            type=User.UserType.SYSTEM_ADMIN, # type: ignore
        )
        
        sysadmin = SystemAdmin.objects.get(id=sysadmin_user.id) # type: ignore
        self.assertEqual(sysadmin.type, User.UserType.SYSTEM_ADMIN) # type: ignore

class PatientFunctionTest(BaseModelTest):
    def setUp(self):
        super().setUp()
        
        self.patient_user = User.objects.create_user(
            username="test",
            password="password1234",
            email="test@example.com",
            type=User.UserType.PATIENT, # type: ignore
            first_name="Test",
            last_name="User"
        )
        
        self.patient_profile = PatientProfile.objects.create(
            user=self.patient_user,
            age=25,
            blood_type="A+"
        )
        
        self.patient = Patient.objects.get(id=self.patient_user.id) # type: ignore
        
        # Create healthcare provider
        self.provider_user = User.objects.create_user(
            username="doc",
            password="password1234",
            email="doc@example.com",
            type=User.UserType.HEALTHCARE_PROVIDER, # type: ignore
            first_name="Doc",
            last_name="User"
        )
        
        self.provider_profile = HealthcareProviderProfile.objects.create(
            user=self.provider_user,
            speciality=self.speciality,
            image="doctor.jpg",
            education="MD",
            years_of_experience=5,
            about="Test doctor",
            fees=100.,
            address_line1="123 Test St",
            city="Test City",
            state="TS",
            zip_code="12345",
            license_number="MD654321",
            primary_hospital=self.hospital
        )
        
        self.provider = HealthcareProvider.objects.get(id=self.provider_user.id) # type: ignore
        
    def test_patient_view_doctors(self):
        doctors = self.patient.view_healthcare_providers() # type: ignore
        self.assertEqual(doctors.count(), 1)
        self.assertEqual(doctors.first(), self.provider)
        
    def test_patient_search_doctors(self):
        """Test patient can search doctors by speciality"""
        # Search with matching speciality
        doctors = self.patient.search_healthcare_providers(speciality="Gynecologist") # type: ignore
        self.assertEqual(doctors.count(), 1)
        
        # Search with non-matching speciality
        doctors = self.patient.search_healthcare_providers(speciality="Dermatology") # type: ignore
        self.assertEqual(doctors.count(), 0)
        
        # Search without speciality
        doctors = self.patient.search_healthcare_providers()
        self.assertEqual(doctors.count(), 1)
        
    def test_patient_schedule_appointment(self):
        start_time = timezone.now() + timedelta(days=1)
        end_time = timezone.now() + timedelta(days=2)
        
        appointment = self.patient.schedule_appointment(
            healthcare_providers=self.provider,
            start_datetime_utc=start_time,
            end_datetime_utc=end_time,
            reason="Test"
        )
        
        self.assertEqual(appointment.patient, self.patient)
        self.assertEqual(appointment.healthcare_provider, self.provider)
        self.assertEqual(appointment.status, Appointment.Status.REQUESTED)
        self.assertEqual(appointment.reason, "Test")

    def test_patient_schedule_past_appointment(self):
        start_time = timezone.now() - timedelta(days=1)
        end_time = timezone.now() + timedelta(days=1)
        
        with self.assertRaises(ValidationError):
            self.patient.schedule_appointment(
                healthcare_providers=self.provider,
                start_datetime_utc=start_time,
                end_datetime_utc=end_time,
                reason="Test"
            )







# class UserModelTest(TestCase):
#     def setUp(self):
#         self.user_data = {
#             "email": "alice@example.com",
#             "date_of_birth": "1980-10-12",
#             "password": "abc123",
#             "first_name": "Alice",
#             "last_name": "Perez"
#         }
        
#     def test_create_user(self):
#         user = User.objects.create_user(**self.user_data)
#         self.assertEqual(user.email, self.user_data["email"])
#         self.assertEqual(user.date_of_birth, self.user_data["date_of_birth"])
#         self.assertTrue(user.check_password(self.user_data["password"]))
#         self.assertEqual(user.first_name, self.user_data["first_name"])
#         self.assertEqual(user.last_name, self.user_data["last_name"])
#         self.assertTrue(user.is_active)
#         self.assertFalse(user.is_admin)
        
#     def test_create_super_user(self):
#         admin_user = User.objects.create_superuser(
#             email="admin@example.com",
#             password="109m3!jT+",
#             first_name="Jason",
#             last_name="Li",
#             date_of_birth="1992-04-22",
#         )
#         self.assertTrue(admin_user.is_admin)
#         self.assertTrue(admin_user.is_staff)
        
#     def test_user_str_representation(self):
#         user = User.objects.create_user(**self.user_data)
#         self.assertEqual(str(user), self.user_data["email"])
        
# class SpecialityModelTest(TestCase):
#     def setUp(self):
#         self.specialities = {
#             "name": "General physician",
#             "image": "test.svg"
#         }

#     def test_create_speciality(self):
#         speciality = Speciality.objects.create(**self.specialities)
#         self.assertEqual(str(speciality), "General physician")
        
# class DoctorModelTest(TestCase):
#     def setUp(self):
#         self.gynecologist = Speciality.objects.create(
#             name="Gynecologist",
#             image="img.svg"
#         )
#         self.doctor = {
#             "first_name": "Emily",
#             "last_name": "Larson",
#             "image": "http://127.0.0.1:8000/media/doctors/doc2.png",
#             "speciality": self.gynecologist,
#             "degree": "MD",
#             "experience": 3.,
#             "about": "Board-certified obstetrician and gynecologist Dr. Emily Larson is dedicated to providing exceptional, evidence-based healthcare to women at every stage of life. With three years of experience as a practicing MD following her residency, Dr. Larson combines her extensive medical training with a warm, collaborative approach to patient care.",
#             "fees": 60.,
#             "address_line1": "3656 Longview Avenue",
#             "address_line2": "Suite 202",
#             "city": "Bronx",
#             "state": "NY",
#             "zip_code": "10453"
#         }
    
#     def test_create_doctor(self):
#         doctor = Doctor.objects.create(**self.doctor)
#         self.assertEqual(doctor.speciality, self.gynecologist)
#         self.assertEqual(doctor.degree, "MD")
#         self.assertEqual(doctor.about, self.doctor["about"])
#         self.assertEqual(doctor.address_line1, self.doctor["address_line1"])
#         self.assertEqual(doctor.address_line2, self.doctor["address_line2"])
#         self.assertEqual(doctor.city, self.doctor["city"])
        
#     def test_experience_non_negative_constraint(self):
#         invalid_data = self.doctor.copy()
#         invalid_data["experience"] = -5.
        
#         with self.assertRaises(IntegrityError):
#             Doctor.objects.create(**invalid_data)
            
#     def test_fee_gt_zero_constraint(self):
#         invalid_data = self.doctor.copy()
#         invalid_data["fees"] = 0.
        
#         with self.assertRaises(IntegrityError):
#             Doctor.objects.create(**invalid_data)
        
#     def test_multiple_doctor_same_speciality(self):
#         doctor1 = Doctor.objects.create(**self.doctor)

#         doctor2_data = self.doctor.copy()
#         doctor2_data["first_name"] = "Bob"
#         doctor2 = Doctor.objects.create(**doctor2_data)
        
#         self.assertEqual(Doctor.objects.count(), 2)
#         self.assertEqual(self.gynecologist.doctors.count(), 2)
