# tests/provider/test_views.py
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client():
    return APIClient()

# ------------------------------------------------------------------
#  public list  (GET /api/provider/)
# ------------------------------------------------------------------
class TestProviderList:
    url = "/api/provider/"

    def test_list_only_active(self, api_client, healthcare_provider_factory, user_factory):
        user = user_factory()
        api_client.force_authenticate(user=user)

        healthcare_provider_factory(is_removed=False)
        healthcare_provider_factory(is_removed=True) 
        res = api_client.get(self.url)
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 1 

    def test_search_smoke(self, api_client, healthcare_provider_factory, user_factory):
        user = user_factory()
        api_client.force_authenticate(user=user)

        healthcare_provider_factory(user__first_name="John", about="Cardio specialist")
        res = api_client.get(self.url, {"search": "John"})
        assert res.status_code == status.HTTP_200_OK
        assert res.data[0]["firstName"] == "John"

# ------------------------------------------------------------------
#  public sign-up  (POST /api/provider/)
# ------------------------------------------------------------------
class TestProviderSignUp:
    url = "/api/provider/"

    def test_create_minimal(self, api_client, speciality_factory, admin_staff_factory):
        s = speciality_factory()
        a = admin_staff_factory()

        payload = {
            "email": "doc@new.com",
            "username": "docnew",
            "password": "Complex123!",
            "first_name": "Doc",
            "last_name": "Tor",
            "speciality": s.pk,
            "fees": "120.00",
            "address_line1": "123 Main",
            "city": "Town",
            "state": "CA",
            "zip_code": "12345",
            "license_number": "AB123456",
        }
        api_client.force_authenticate(user=a.user)
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED, res.data
        user = User.objects.get(email="doc@new.com")
        assert hasattr(user, "provider")
        assert user.provider.fees == 120

    def test_user_create_denied(self, api_client, speciality_factory, user_factory):
        s = speciality_factory()
        u = user_factory()

        payload = {
            "email": "doc@new.com",
            "username": "docnew",
            "password": "Complex123!",
            "first_name": "Doc",
            "last_name": "Tor",
            "speciality": s.pk,
            "fees": "120.00",
            "address_line1": "123 Main",
            "city": "Town",
            "state": "CA",
            "zip_code": "12345",
            "license_number": "AB123456",
        }
        api_client.force_authenticate(user=u)
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_speciality_required(self, api_client, admin_staff_factory):
        a = admin_staff_factory()

        payload = {
            "email": "bad@doc.com",
            "username": "bad",
            "password": "Complex123!",
            "first_name": "A",
            "last_name": "B",
            "fees": "100.00",
            "address_line1": "123 Main",
            "city": "Town",
            "state": "CA",
            "zip_code": "12345",
            "license_number": "AB123456",
        }
        api_client.force_authenticate(user=a.user)
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "speciality" in res.data

# ------------------------------------------------------------------
#  onboard existing user 
# ------------------------------------------------------------------
class TestProviderOnBoard:
    url = "/api/provider/onboard/"

    def test_success(self, api_client, admin_staff_factory, speciality_factory, user_factory):
        a = admin_staff_factory()
        user = user_factory()
        api_client.force_authenticate(user=a.user)
        payload = {
            "user": user.pk,
            "speciality": speciality_factory().pk,
            "about": "test",
            "fees": "99.99",
            "address_line1": "456 Oak",
            "city": "Ville",
            "state": "NY",
            "zip_code": "54321",
            "license_number": "XY987654",
        }
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        assert hasattr(user, "provider")
        assert float(user.provider.fees) == 99.99

    def test_user_onboard_denied(self, api_client, user_factory, speciality_factory):
        user = user_factory()
        api_client.force_authenticate(user=user)
        payload = {
            "speciality": speciality_factory().pk,
            "about": "test",
            "fees": "99.99",
            "address_line1": "456 Oak",
            "city": "Ville",
            "state": "NY",
            "zip_code": "54321",
            "license_number": "XY987654",
        }
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_second_profile_rejected(self,
                                     api_client,
                                     healthcare_provider_factory,
                                     admin_staff_factory,
                                     speciality_factory):
        a = admin_staff_factory()
        prov = healthcare_provider_factory()

        api_client.force_authenticate(user=a.user)
        payload = {
            "user": prov.user.pk,
            "speciality": speciality_factory().pk,
            "about": "test",
            "fees": "99.99",
            "address_line1": "456 Oak",
            "city": "Ville",
            "state": "NY",
            "zip_code": "54321",
            "license_number": "XY987654",
        }
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        print('res: ', res.data)
        assert "already exists" in res.data["user"][0]

    def test_anonymous_denied(self, api_client):
        res = api_client.post(self.url, {}, format="json")
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

# ------------------------------------------------------------------
#  profile R / U  (GET/PATCH /api/provider/me/)
# ------------------------------------------------------------------
class TestProviderProfile:
    me_url = "/api/provider/me/"

    def test_retrieve_own(self, api_client, healthcare_provider_factory):
        prov = healthcare_provider_factory(about="Cardio expert")
        api_client.force_authenticate(user=prov.user)
        res = api_client.get(self.me_url)
        assert res.status_code == status.HTTP_200_OK
        assert res.data["about"] == "Cardio expert"

    def test_update_own(self, api_client, healthcare_provider_factory):
        prov = healthcare_provider_factory(fees=100)
        api_client.force_authenticate(user=prov.user)
        payload = {"fees": "150.00"}
        res = api_client.patch(self.me_url, payload, format="json")
        print("res: ", res.data)
        assert res.status_code == status.HTTP_200_OK
        prov.refresh_from_db()
        assert float(prov.fees) == 150.0

    def test_anonymous_denied(self, api_client):
        res = api_client.get(self.me_url)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

# ------------------------------------------------------------------
#  staff soft-delete
# ------------------------------------------------------------------
class TestProviderSoftDelete:
    def test_staff_can_soft_delete(
        self,
        api_client,
        healthcare_provider_factory,
        admin_staff_factory,
        hospital_factory
    ):
        h = hospital_factory()
        staff = admin_staff_factory(hospital=h)
        prov = healthcare_provider_factory(primary_hospital=h, is_removed=False, removed_at=None)
        api_client.force_authenticate(user=staff.user)
        payload = {"is_removed": True}
        url = f"/api/provider/{prov.user.pk}/"

        res = api_client.patch(url, payload, format="json")
        assert res.status_code == status.HTTP_200_OK
        prov.refresh_from_db()
        assert prov.is_removed is True
        assert prov.removed_at is not None

    def test_non_staff_cannot_soft_delete(
        self,
        api_client,
        healthcare_provider_factory,
        patient_factory,
        hospital_factory,
    ):
        h = hospital_factory()
        prov = healthcare_provider_factory(primary_hospital=h, is_removed=False)
        p = patient_factory()
        api_client.force_authenticate(user=p.user)
        payload = {"is_removed": True}
        url = f"/api/provider/{prov.user.pk}/"

        res = api_client.patch(url, payload, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN
