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


# ------------------------------------------------------------------
#  profile update
# ------------------------------------------------------------------
class TestPatientUpdate:
    def get_patient_detail_url(self, user_id=1):
        """Helper to get patient detail URL - ID doesn't matter due to get_object() override"""
        print(f"user id: {user_id}")
        return f"/api/patient/{user_id}/"

    def test_patient_can_update_own_profile(self, api_client, patient_factory):
        """Test patient can update their own profile with PATCH"""
        p = patient_factory(weight=60, blood_type="O+")
        api_client.force_authenticate(user=p.user)

        payload = {
            "weight": 65,
            "height": 180,
            "allergies": "Peanuts, Penicillin",
            "chronicConditions": "Asthma",
            "currentMedications": "Ventolin",
        }

        res = api_client.patch(self.get_patient_detail_url(), payload, format="json")
        assert res.status_code == status.HTTP_200_OK, res.data

        p.refresh_from_db()
        assert p.weight == 65
        assert p.height == 180
        assert p.allergies == "Peanuts, Penicillin"
        assert p.chronic_conditions == "Asthma"
        assert p.current_medications == "Ventolin"

    def test_patient_can_update_user_profile_through_patient(
        self, api_client, patient_factory
    ):
        """Test that patient can update user fields through patient update"""
        p = patient_factory()
        api_client.force_authenticate(user=p.user)

        payload = {
            "user": {
                "first_name": "Updated",
                "last_name": "Name",
                "phone_number": "+1234567890",
                "date_of_birth": "1990-01-01",
                "address_line1": "123 Updated St",
            }
        }

        res = api_client.patch(self.get_patient_detail_url(), payload, format="json")
        assert res.status_code == status.HTTP_200_OK, res.data

        p.refresh_from_db()
        p.user.refresh_from_db()
        assert p.user.first_name == "Updated"
        assert p.user.last_name == "Name"
        assert p.user.phone_number == "+1234567890"
        assert str(p.user.date_of_birth) == "1990-01-01"
        assert p.user.address_line1 == "123 Updated St"

    def test_patient_cannot_update_other_patient_profile(
        self, api_client, patient_factory
    ):
        """Test that a patient cannot update another patient's profile"""
        p1 = patient_factory(weight=60)
        p2 = patient_factory(weight=70)

        api_client.force_authenticate(user=p1.user)

        payload = {"weight": 65}
        api_client.patch(
            self.get_patient_detail_url(p2.user.id), payload, format="json"
        )

        p1.refresh_from_db()
        p2.refresh_from_db()
        # p1 should be updated, p2 should remain unchanged
        assert p1.weight == 65
        assert p2.weight == 70

    def test_update_with_negative_weight_validation(self, api_client, patient_factory):
        """Test validation for negative weight"""
        p = patient_factory(weight=60)
        api_client.force_authenticate(user=p.user)

        payload = {"weight": -10}
        res = api_client.patch(self.get_patient_detail_url(), payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "weight" in res.data
        assert "greater than or equal to 0" in str(res.data["weight"])

    def test_update_empty_payload_does_nothing(self, api_client, patient_factory):
        """Test that empty PATCH payload doesn't change anything"""
        p = patient_factory(weight=60, height=170, blood_type="O+")
        api_client.force_authenticate(user=p.user)

        original_weight = p.weight
        original_height = p.height
        original_blood_type = p.blood_type

        res = api_client.patch(self.get_patient_detail_url(), {}, format="json")
        assert res.status_code == status.HTTP_200_OK, res.data

        p.refresh_from_db()
        assert p.weight == original_weight
        assert p.height == original_height
        assert p.blood_type == original_blood_type
