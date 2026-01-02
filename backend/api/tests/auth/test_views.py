import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client():
    return APIClient()

# ==================================================================
#  login
# ==================================================================
class TestLogin:
    url = "/api/auth/login/"

    def test_success(self, api_client, user_factory):
        user = user_factory(email="active@user.com")
        user.set_password("Secret123!")
        user.is_active = True
        user.save()
        payload = {"email": "active@user.com", "password": "Secret123!"}
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_200_OK
        assert "access" in res.data
        assert "refresh" in res.data
        assert res.data["user"]["id"] == user.pk

    def test_wrong_password(self, api_client, user_factory):
        user = user_factory(email="bad@user.com")
        user.set_password("RightPass123!")
        user.is_active = True
        user.save()
        payload = {"email": "bad@user.com", "password": "WrongPass!"}
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_401_UNAUTHORIZED
        assert res.data["detail"] == "Invalid credentials"

    def test_inactive_user(self, api_client, user_factory):
        user = user_factory(email="inactive@user.com")
        user.set_password("Secret123!")
        user.is_active = False
        user.save()
        payload = {"email": "inactive@user.com", "password": "Secret123!"}
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN
        assert res.data["detail"] == "E-mail not verified"

    def test_missing_field(self, api_client):
        res = api_client.post(self.url, {"email": "only@mail.com"}, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in res.data

# ==================================================================
#  verify email
# ==================================================================
class TestVerifyEmail:
    url = "/api/auth/verify/{key}/"

    def test_success(self, api_client, user_factory):
        user = user_factory(email="verify@user.com", is_active=False)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        key = f"{uid}-{token}"
        res = api_client.get(self.url.format(key=key))
        assert res.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.is_active

    def test_bad_token(self, api_client):
        res = api_client.get(self.url.format(key="bad-token"))
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert res.data["detail"] == "Bad link"


# ==================================================================
#  resend verification
# ==================================================================
class TestResendVerify:
    url = "/api/auth/resend-verify/"

    def test_success(self, api_client, user_factory):
        user = user_factory(email="resend@user.com", is_active=False)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        res = api_client.post(self.url, {"uid": uid}, format="json")
        assert res.status_code == status.HTTP_204_NO_CONTENT

    def test_resend_active_user(self, api_client, user_factory):
        user = user_factory(email="active@user.com", is_active=True)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        res = api_client.post(self.url, {"uid": uid}, format="json")
        assert res.status_code == status.HTTP_204_NO_CONTENT  # silent success

    def test_bad_uid(self, api_client):
        res = api_client.post(self.url, {"uid": "bad-uid"}, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert res.data["detail"] == "Invalid uid"

# ==================================================================
#  logout
# ==================================================================
class TestLogout:
    url = "/api/auth/logout/"

    def test_success(self, api_client, user_factory):
        user = user_factory()
        res = api_client.post("/api/auth/login/", {"email": user.email, "password": "complex123!"}, format="json")
        refresh = res.data["refresh"]
        api_client.force_authenticate(user=user)
        res = api_client.post(self.url, {"refresh": refresh}, format="json")
        assert res.status_code == status.HTTP_205_RESET_CONTENT

    def test_missing_token(self, api_client, user_factory):
        user = user_factory()
        api_client.force_authenticate(user=user)
        res = api_client.post(self.url, {}, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST

# ==================================================================
#  change password
# ==================================================================
class TestChangePassword:
    url = "/api/auth/change-password/"

    def test_success(self, api_client, user_factory):
        user = user_factory()
        user.set_password("OldPass123!")
        user.save()
        api_client.force_authenticate(user=user)
        payload = {"old_password": "OldPass123!", "new_password": "NewPass456!"}
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password("NewPass456!")

    def test_wrong_old_password(self, api_client, user_factory):
        user = user_factory()
        user.set_password("RightPass123!")
        user.save()
        api_client.force_authenticate(user=user)
        payload = {"old_password": "WrongPass!", "new_password": "NewPass456!"}
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert res.data["detail"] == "Old password is incorrect."

    def test_anonymous_denied(self, api_client):
        res = api_client.post(self.url, {}, format="json")
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

# ==================================================================
#  me
# ==================================================================
class TestUserMe:
    url = "/api/auth/me/"

    def test_retrieve(self, api_client, user_factory):
        user = user_factory()
        api_client.force_authenticate(user=user)
        res = api_client.get(self.url)
        assert res.status_code == status.HTTP_200_OK
        assert res.data["id"] == str(user.pk)
        assert res.data["email"] == user.email

    def test_anonymous_denied(self, api_client):
        res = api_client.get(self.url)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED