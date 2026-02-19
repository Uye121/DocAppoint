import pytest
from django.contrib.auth import get_user_model
from ...serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
)

User = get_user_model()
pytestmark = pytest.mark.django_db


# ==================================================================
#  ChangePasswordSerializer
# ==================================================================
class TestChangePasswordSerializer:
    def test_valid_payload(self):
        payload = {"old_password": "OldPass123!", "new_password": "NewPass456!"}
        ss = ChangePasswordSerializer(data=payload)
        assert ss.is_valid(), ss.errors

    def test_old_password_missing(self):
        payload = {"new_password": "NewPass456!"}
        ss = ChangePasswordSerializer(data=payload)
        assert not ss.is_valid()
        assert "old_password" in ss.errors

    def test_new_password_missing(self):
        payload = {"old_password": "OldPass123!"}
        ss = ChangePasswordSerializer(data=payload)
        assert not ss.is_valid()
        assert "new_password" in ss.errors


# ==================================================================
#  LoginSerializer
# ==================================================================
class TestLoginSerializer:
    def test_valid_credentials(self, user_factory):
        user = user_factory(email="active@user.com")
        user.set_password("Secret123!")
        user.is_active = True
        user.save()

        user.refresh_from_db()
        payload = {"email": "active@user.com", "password": "Secret123!"}
        ss = LoginSerializer(data=payload)
        assert ss.is_valid(), ss.errors
        assert ss.validated_data["user"] == user

    def test_invalid_password(self, user_factory):
        user = user_factory(email="bad@user.com")
        user.set_password("Secret123!")
        user.is_active = True
        user.save()
        payload = {"email": "bad@user.com", "password": "WrongPass!"}
        ss = LoginSerializer(data=payload)
        assert not ss.is_valid()
        assert "non_field_errors" in ss.errors

    def test_inactive_user(self, user_factory):
        user = user_factory(email="inactive@user.com")
        user.set_password("Secret123!")
        user.is_active = False
        user.save()
        payload = {"email": "inactive@user.com", "password": "Secret123!"}
        ss = LoginSerializer(data=payload)
        assert not ss.is_valid()
        assert "non_field_errors" in ss.errors

    def test_email_missing(self):
        payload = {"password": "Secret123!"}
        ss = LoginSerializer(data=payload)
        assert not ss.is_valid()
        assert "email" in ss.errors

    def test_password_missing(self):
        payload = {"email": "missing@user.com"}
        ss = LoginSerializer(data=payload)
        assert not ss.is_valid()
        assert "password" in ss.errors
