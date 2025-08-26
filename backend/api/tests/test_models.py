import os
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from ..models import Speciality, Doctor

User = get_user_model()

class UserModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            "email": "alice@example.com",
            "date_of_birth": "1980-10-12",
            "password": "abc123",
            "first_name": "Alice",
            "last_name": "Perez"
        }
        
    def test_create_user(self):
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, self.user_data["email"])
        self.assertEqual(user.date_of_birth, self.user_data["date_of_birth"])
        self.assertTrue(user.check_password(self.user_data["password"]))
        self.assertEqual(user.first_name, self.user_data["first_name"])
        self.assertEqual(user.last_name, self.user_data["last_name"])
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_admin)
        
    def test_create_super_user(self):
        admin_user = User.objects.create_superuser(
            email="admin@example.com",
            password="109m3!jT+",
            first_name="Jason",
            last_name="Li",
            date_of_birth="1992-04-22",
        )
        self.assertTrue(admin_user.is_admin)
        self.assertTrue(admin_user.is_staff)
        
    def test_user_str_representation(self):
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), self.user_data["email"])
        
class SpecialityModelTest(TestCase):
    def setUp(self):
        self.specialities = {
            "name": "General physician",
            "image": "test.svg"
        }

    def test_create_speciality(self):
        speciality = Speciality.objects.create(**self.specialities)
        self.assertEqual(str(speciality), "General physician")
        
class DoctorModelTest(TestCase):
    def setUp(self):
        self.gynecologist = Speciality.objects.create(
            name="Gynecologist",
            image="img.svg"
        )
        self.doctor = {
            "first_name": "Emily",
            "last_name": "Larson",
            "image": "http://127.0.0.1:8000/media/doctors/doc2.png",
            "speciality": self.gynecologist,
            "degree": "MD",
            "experience": 3.,
            "about": "Board-certified obstetrician and gynecologist Dr. Emily Larson is dedicated to providing exceptional, evidence-based healthcare to women at every stage of life. With three years of experience as a practicing MD following her residency, Dr. Larson combines her extensive medical training with a warm, collaborative approach to patient care.",
            "fees": 60.,
            "address_line1": "3656 Longview Avenue",
            "address_line2": "Suite 202",
            "city": "Bronx",
            "state": "NY",
            "zip_code": "10453"
        }
    
    def test_create_doctor(self):
        doctor = Doctor.objects.create(**self.doctor)
        self.assertEqual(doctor.formatted_experience, "3.0 Years")
        self.assertEqual(doctor.formatted_name, "Dr. Emily Larson")
        self.assertEqual(doctor.speciality, self.gynecologist)
        self.assertEqual(doctor.degree, "MD")
        self.assertEqual(doctor.about, self.doctor["about"])
        self.assertEqual(doctor.address_line1, self.doctor["address_line1"])
        self.assertEqual(doctor.address_line2, self.doctor["address_line2"])
        self.assertEqual(doctor.city, self.doctor["city"])
        
    def test_experience_non_negative_constraint(self):
        invalid_data = self.doctor.copy()
        invalid_data["experience"] = -5.
        
        with self.assertRaises(IntegrityError):
            Doctor.objects.create(**invalid_data)
            
    def test_fee_gt_zero_constraint(self):
        invalid_data = self.doctor.copy()
        invalid_data["fees"] = 0.
        
        with self.assertRaises(IntegrityError):
            Doctor.objects.create(**invalid_data)
        
    def test_multiple_doctor_same_speciality(self):
        doctor1 = Doctor.objects.create(**self.doctor)

        doctor2_data = self.doctor.copy()
        doctor2_data["first_name"] = "Bob"
        doctor2 = Doctor.objects.create(**doctor2_data)
        
        self.assertEqual(Doctor.objects.count(), 2)
        self.assertEqual(self.gynecologist.doctors.count(), 2)
