import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def api_client():
    return APIClient()


# ------------------------------------------------------------------
#  public sign-up
# ------------------------------------------------------------------
class TestPatientSignUp:
    url = "/api/patient/"

    def test_create_minimal(self, api_client):
        payload = {
            "email": "new@patient.com",
            "username": "newpatient",
            "password": "Complex123!",
            "first_name": "Neo",
            "last_name": "Patient",
            "blood_type": "O+",
            "weight": 80,
            "height": 190,
        }
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED, res.data
        user = User.objects.get(email="new@patient.com")
        assert hasattr(user, "patient")
        assert user.patient.weight == 80

    def test_email_duplicate(self, api_client, user_factory):
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


# ------------------------------------------------------------------
#  onboard existing user
# ------------------------------------------------------------------
class TestPatientOnBoard:
    url = "/api/patient/onboard/"

    def test_success(self, api_client, user_factory):
        user = user_factory()
        api_client.force_authenticate(user=user)
        payload = {"blood_type": "A+", "weight": 70, "height": 175}
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        assert hasattr(user, "patient")
        assert user.patient.blood_type == "A+"

    def test_second_profile_rejected(self, api_client, patient_factory):
        pat = patient_factory()
        api_client.force_authenticate(user=pat.user)
        payload = {"weight": 80}
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in res.data["detail"]

    def test_anonymous_denied(self, api_client):
        res = api_client.post(self.url, {}, format="json")
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


# ------------------------------------------------------------------
#  profile
# ------------------------------------------------------------------
class TestPatientProfile:
    me_url = "/api/patient/me/"

    def test_retrieve_own(self, api_client, patient_factory):
        p = patient_factory(blood_type="B-")
        api_client.force_authenticate(user=p.user)
        res = api_client.get(self.me_url)
        assert res.status_code == status.HTTP_200_OK
        assert res.data["bloodType"] == "B-"

    def test_update_own(self, api_client, patient_factory):
        p = patient_factory(weight=60)
        api_client.force_authenticate(user=p.user)
        payload = {"weight": 65}
        res = api_client.patch(self.me_url, payload, format="json")
        assert res.status_code == status.HTTP_200_OK
        p.refresh_from_db()
        assert p.weight == 65

    def test_anonymous_denied(self, api_client):
        res = api_client.get(self.me_url)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


# ------------------------------------------------------------------
#  staff list
# ------------------------------------------------------------------
class TestPatientList:
    url = "/api/patient/"

    def test_staff_can_list(self, api_client, patient_factory, user_factory):
        staff_user = user_factory(is_staff=True)
        patient_factory()
        patient_factory()
        api_client.force_authenticate(user=staff_user)
        res = api_client.get(self.url)
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 2  # paginated response

    def test_non_staff_forbidden(self, api_client, patient_factory, user_factory):
        normal_user = user_factory(is_staff=False)
        patient_factory()
        api_client.force_authenticate(user=normal_user)
        res = api_client.get(self.url)
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_anonymous_forbidden(self, api_client):
        res = api_client.get(self.url)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED
