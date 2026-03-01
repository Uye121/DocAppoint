import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.test import override_settings

from api.models import User

pytestmark = pytest.mark.django_db


class TestUserRegistrationFlow:
    """Test user registration without patient/provider role"""

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_regular_user_signup(self, mailoutbox):
        """Test a user signing up without a patient/provider profile"""
        url = reverse("users-list")
        user_data = {
            "email": "regular@example.com",
            "username": "regularuser",
            "password": "ComplexPass123!",
            "first_name": "Regular",
            "last_name": "User",
        }
        api_client = APIClient()

        response = api_client.post(url, user_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        user = User.objects.get(email="regular@example.com")
        assert not user.is_active  # Inactive until email verified
        assert not hasattr(user, "patient")
        assert not hasattr(user, "provider")

        # Verify email sent
        assert len(mailoutbox) == 1


class TestUserProfileWithoutRole:
    """Test users without patient/provider roles"""

    def test_user_can_view_own_profile(self, user_factory):
        """Test regular user can view their profile"""
        user = user_factory(is_active=True)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse("users-me")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user.email
        assert response.data["userRole"] == "unassigned"
        assert not response.data["hasPatientProfile"]
        assert not response.data["hasProviderProfile"]

    def test_user_can_update_own_profile(self, user_factory):
        """Test regular user can update their profile"""
        user = user_factory(first_name="Old", is_active=True)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse("users-me")
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "phone_number": "1234567890",
        }

        response = api_client.patch(url, update_data, format="json")
        assert response.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        assert user.first_name == "Updated"
        assert user.last_name == "Name"


class TestUserRoleProgression:
    """Test users gaining roles after initial signup"""

    def test_user_signs_up_then_becomes_patient(self):
        """Test flow: sign up as regular user → onboard as patient"""
        # Sign up as regular user
        register_url = reverse("users-list")
        user_data = {
            "email": "progressive@example.com",
            "username": "progressive",
            "password": "ComplexPass123!",
            "first_name": "Progressive",
            "last_name": "User",
        }
        api_client = APIClient()

        response = api_client.post(register_url, user_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        user_id = response.data["id"]

        # Verify email manually
        user = User.objects.get(id=user_id)
        user.is_active = True
        user.save()

        login_url = reverse("login")
        login_response = api_client.post(
            login_url,
            {"email": "progressive@example.com", "password": "ComplexPass123!"},
            format="json",
        )
        assert login_response.status_code == status.HTTP_200_OK
        token = login_response.data["access"]

        # Onboard as patient
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        onboard_url = reverse("patient-on-board")
        patient_data = {"blood_type": "O+", "allergies": "None", "weight": 70}

        response = api_client.post(onboard_url, patient_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        # Verify user now has patient profile
        user.refresh_from_db()
        assert hasattr(user, "patient")
        assert user.patient.blood_type == "O+"
