import pytest
import time
from django.contrib.auth import get_user_model
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient
from rest_framework import status

from ...utils.tokens import build_verification_jwt

User = get_user_model()

pytestmark = pytest.mark.django_db(transaction=True)

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
        assert res.data["user"]["id"] == str(user.pk)

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
    url = "/api/auth/verify/"

    def test_success(self, api_client, user_factory):
        user = user_factory(email="verify@user.com", is_active=False)
        token = build_verification_jwt(user)
        res = api_client.get(self.url, {"token": token})
        assert res.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.is_active

    def test_bad_token(self, api_client):
        res = api_client.get(self.url, {"token": "bad-token"})
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert res.data["detail"] == "Bad or expired token"

# ==================================================================
#  resend verification
# ==================================================================
class TestResendVerify:
    url = "/api/auth/resend-verify/"

    def test_success(self, api_client, user_factory):
        user = user_factory(email="resend@user.com", is_active=False)
        res = api_client.post(self.url, {"email": user.email}, format="json")
        assert res.status_code == status.HTTP_204_NO_CONTENT

    def test_second_resend_invalidates_previous_token(
        self, api_client, user_factory
    ):
        user = user_factory(email="tok@inv.com", is_active=False)

        # first resend
        res = api_client.post(self.url, {"email": user.email}, format="json")
        assert res.status_code == status.HTTP_204_NO_CONTENT
        user.refresh_from_db()
        token_a = build_verification_jwt(user)   # captured “old” token
        old_ts = user.reset_sent_at

        time.sleep(2)

        # second resend
        res = api_client.post(self.url, {"email": user.email}, format="json")
        assert res.status_code == status.HTTP_204_NO_CONTENT
        user.refresh_from_db()
        assert user.reset_sent_at > old_ts 

        # reject first token
        bad = api_client.get("/api/auth/verify/", {"token": token_a})
        assert bad.status_code == status.HTTP_400_BAD_REQUEST
        assert "bad or expired token" in bad.data["detail"].lower()

        # second token works
        user.refresh_from_db()
        token_b = build_verification_jwt(user)
        good = api_client.get("/api/auth/verify/", {"token": token_b})
        assert good.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.is_active

    def test_resend_active_user(self, api_client, user_factory):
        user = user_factory(email="active@user.com", is_active=True)
        res = api_client.post(self.url, {"email": user.email}, format="json")
        print(res.data)
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_email(self, api_client):
        res = api_client.post(self.url, {"email": "bademail@abc.com"}, format="json")
        assert res.status_code == status.HTTP_404_NOT_FOUND
        assert "No User matches the given query." in res.data["detail"]

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