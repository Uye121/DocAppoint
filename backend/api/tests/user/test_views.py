import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def api_client():
    return APIClient()


# ==================================================================
# sign-up
# ==================================================================
class TestUserSignUp:
    url = "/api/users/"

    def test_create_minimal(self, api_client):
        payload = {
            "email": "new@user.com",
            "username": "newuser",
            "password": "Complex123!",
            "first_name": "New",
            "last_name": "User",
        }
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED, res.data
        user = User.objects.get(email="new@user.com")
        assert user.check_password("Complex123!")
        assert not user.is_active

    def test_email_duplicate_case_insensitive(self, api_client, user_factory):
        user_factory(email="EXIST@example.com")
        payload = {
            "email": "exist@example.com",
            "username": "new",
            "password": "Complex123!",
            "first_name": "A",
            "last_name": "B",
        }
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in res.data

    def test_password_blank(self, api_client):
        payload = {
            "email": "bad@user.com",
            "username": "bad",
            "password": "",
            "first_name": "A",
            "last_name": "B",
        }
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in res.data


# ==================================================================
# profile
# ==================================================================
class TestUserProfile:
    url = "/api/users/me/"

    def test_retrieve_own_profile(self, api_client, user_factory):
        user = user_factory()
        api_client.force_authenticate(user=user)
        res = api_client.get(self.url)
        assert res.status_code == status.HTTP_200_OK
        assert res.data["email"] == user.email
        assert res.data["username"] == user.username

    def test_update_own_profile(self, api_client, user_factory):
        user = user_factory(first_name="Old")
        api_client.force_authenticate(user=user)
        payload = {"first_name": "Updated", "phone_number": "+123456"}
        res = api_client.patch(self.url, payload, format="json")
        assert res.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.first_name == "Updated"
        assert user.phone_number == "+123456"

    def test_anonymous_denied(self, api_client):
        res = api_client.get(self.url)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


# ==================================================================
# change-password
# ==================================================================
class TestChangePassword:
    url = "/api/users/change-password/"

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
        assert "old_password" in res.data

    def test_anonymous_denied(self, api_client):
        payload = {"old_password": "x", "new_password": "y"}
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_401_UNAUTHORIZED
