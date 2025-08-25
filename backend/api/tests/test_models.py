from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
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