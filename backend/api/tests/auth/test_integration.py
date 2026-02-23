import re
import jwt
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.test import override_settings 
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

from api.models import User
from api.services.auth import build_verification_jwt

pytestmark = pytest.mark.django_db

class TestAuthenticationFlow:

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_user_registration_and_verification_flow(self, mailoutbox):
        """Test complete flow: user registers -> receives email -> verifies -> becomes active"""
        register_url = reverse("users-list")
        
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "ComplexPass123!",
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-01",
            "phone_number": "+1234567890"
        }

        api_client = APIClient()
        response = api_client.post(register_url, user_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        
        user_id = response.data["id"]
        user = User.objects.get(id=user_id)
        
        # Verify user is created but inactive
        assert not user.is_active
        assert user.email == "newuser@example.com"
        assert user.reset_sent_at is not None
        
        # Verify email was printed to console (dev)
        assert len(mailoutbox) == 1
        email = mailoutbox[0]
        assert email.to == ["newuser@example.com"]
        assert "Confirmation Email" in email.subject

        assert len(email.alternatives) > 0

        html_content = email.alternatives[0][0]
        content_type = email.alternatives[0][1]
        assert content_type == 'text/html'

        # Extract token from email
        token_match = re.search(r'href=[\'"]?[^\'">]*/verify-email\?token=([^\'"\s>]+)', html_content)
        assert token_match is not None
        token = token_match.group(1)

        login_url = reverse("login")
        login_data = {
            "email": "newuser@example.com",
            "password": "ComplexPass123!"
        }
        response = api_client.post(login_url, login_data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "E-mail not verified" in response.data["detail"]
        
        verify_url = reverse("verify_email")
        response = api_client.get(f"{verify_url}?token={token}")
        assert response.status_code == status.HTTP_200_OK
        assert "E-mail verified" in response.data["detail"]
        
        # Verify user is now active
        user.refresh_from_db()
        assert user.is_active
        
        # Step 5: Login after verification - should succeed
        response = api_client.post(login_url, login_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert "user" in response.data
        assert response.data["user"]["email"] == "newuser@example.com"

    def test_password_change_flow(self, authenticated_user_client):
        """Test complete password change flow for authenticated user"""
        client, user = authenticated_user_client()
        
        change_password_url = reverse("users-change-password")
        login_url = reverse("login")
        
        # Try changing password with wrong old password
        wrong_data = {
            "old_password": "wrongpassword",
            "new_password": "NewComplexPass123!"
        }
        response = client.post(change_password_url, wrong_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Wrong password" in response.data["old_password"]
        
        # Change password with correct old password
        correct_data = {
            "old_password": "complex123!",
            "new_password": "NewComplexPass123!"
        }
        response = client.post(change_password_url, correct_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "Password updated" in response.data["detail"]
        
        # Verify can login with new password
        user.refresh_from_db()
        assert user.check_password("NewComplexPass123!")

        login_url = reverse("login")
        login_data = {
            "email": user.email,
            "password": "NewComplexPass123!"
        }
        response = client.post(login_url, login_data, format="json")
        assert response.status_code == status.HTTP_200_OK

        old_login_data = {
            "email": user.email,
            "password": "complex123!"
        }
        response = client.post(login_url, old_login_data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_flow(self, authenticated_user_client):
        """Test logout with token blacklisting"""
        client, user = authenticated_user_client()

        login_url = reverse("login")
        login_data = {
            "email": user.email,
            "password": "complex123!"
        }
        response = client.post(login_url, login_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        refresh_token = response.data["refresh"]
        access_token = response.data["access"]
        
        # Logout with valid refresh token
        logout_url = reverse("logout")
        response = client.post(logout_url, {"refresh": refresh_token}, format="json")
        assert response.status_code == status.HTTP_205_RESET_CONTENT
        
        # Try to refresh token - should fail (token blacklisted)
        refresh_url = reverse("token_refresh")
        response = client.post(refresh_url, {"refresh": refresh_token}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Try to use access token - should still work until expiration
        # (token not blacklisted, just refresh token is)
        me_url = reverse("users-me")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = client.get(me_url)
        assert response.status_code == status.HTTP_200_OK

    def test_concurrent_session_management(self, user_factory):
        """Test multiple sessions for same user"""
        user = user_factory(is_active=True)
        api_client = APIClient()
        
        login_url = reverse("login")
        login_data = {
            "email": user.email,
            "password": "complex123!"
        }
        
        # Login from first client
        response1 = api_client.post(login_url, login_data, format="json")
        assert response1.status_code == status.HTTP_200_OK
        token1 = response1.data["access"]
        
        # Login from second client (different session)
        client2 = api_client.__class__()
        response2 = client2.post(login_url, login_data, format="json")
        assert response2.status_code == status.HTTP_200_OK
        token2 = response2.data["access"]

        me_url = reverse("users-me")
        
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token1}")
        response = api_client.get(me_url)
        assert response.status_code == status.HTTP_200_OK
        
        client2.credentials(HTTP_AUTHORIZATION=f"Bearer {token2}")
        response = client2.get(me_url)
        assert response.status_code == status.HTTP_200_OK

    def test_invalid_login_attempts(self, user_factory):
        """Test various invalid login scenarios"""
        user = user_factory(is_active=True)
        api_client = APIClient()
        login_url = reverse("login")
        
        scenarios = [
            {
                "data": {"email": user.email, "password": "wrongpass"},
                "expected_status": status.HTTP_401_UNAUTHORIZED,
                "expected_msg": "Invalid credentials"
            },
            {
                "data": {"email": "nonexistent@example.com", "password": "anypass"},
                "expected_status": status.HTTP_401_UNAUTHORIZED,
                "expected_msg": "Invalid credentials"
            },
            {
                "data": {"email": user.email},  # Missing password
                "expected_status": status.HTTP_400_BAD_REQUEST,
                "expected_msg": "Missing email or password"
            },
            {
                "data": {"password": "somepass"},  # Missing email
                "expected_status": status.HTTP_400_BAD_REQUEST,
                "expected_msg": "Missing email or password"
            }
        ]
        
        for scenario in scenarios:
            response = api_client.post(login_url, scenario["data"], format="json")
            assert response.status_code == scenario["expected_status"]
            if scenario.get("expected_msg"):
                assert scenario["expected_msg"].lower() in response.data["detail"].lower()

    def test_provider_patient_onboarding_after_verification(self, user_factory, speciality_factory):
        """Test flow: user verifies email -> then creates provider/patient profile"""
        user = user_factory(is_active=False)
        api_client = APIClient()
        
        from api.services.auth import build_verification_jwt
        token = build_verification_jwt(user)
        
        verify_url = reverse("verify_email")
        response = api_client.get(f"{verify_url}?token={token}")
        assert response.status_code == status.HTTP_200_OK
        
        user.refresh_from_db()
        assert user.is_active
        
        # Login with verified user
        login_url = reverse("login")
        login_data = {
            "email": user.email,
            "password": "complex123!"
        }
        response = api_client.post(login_url, login_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        access_token = response.data["access"]
        
        # Create patient profile
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        
        patient_onboard_url = reverse("patient-on-board")
        patient_data = {
            "blood_type": "O+",
            "allergies": "Peanuts",
            "chronic_conditions": "None",
            "current_medications": "None",
            "insurance": "Blue Cross",
            "weight": 70,
            "height": 175
        }
        
        response = api_client.post(patient_onboard_url, patient_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify patient profile created
        assert hasattr(user, "patient")
        assert user.patient.blood_type == "O+"
        
        # Try to create provider profile with same user - should fail
        provider_onboard_url = reverse("provider-onboard")
        speciality = speciality_factory()
        provider_data = {
            "user": user.id,
            "speciality": speciality.pk,
            "about": "Test provider",
            "fees": "100.00",
            "address_line1": "123 Main St",
            "city": "City",
            "state": "CA",
            "zip_code": "12345",
            "license_number": "ABC123456"
        }
        
        response = api_client.post(provider_onboard_url, provider_data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_expired_verification_token(self, user_factory):
        """Test verification with expired token"""
        user = user_factory(is_active=False)
        api_client = APIClient()
        
        # Create a token that's already expired by manipulating the payload
        expired_payload = {
            'user_id': str(user.id),
            'exp': timezone.now() - timedelta(minutes=1),  # Expired 1 minute ago
            'type': 'email_verification'
        }
        expired_token = jwt.encode(
            expired_payload, 
            settings.SECRET_KEY, 
            algorithm='HS256'
        )
        
        verify_url = reverse("verify_email")
        response = api_client.get(f"{verify_url}?token={expired_token}")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Bad or expired token" in response.data["detail"]