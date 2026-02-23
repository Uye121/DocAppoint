# tests/provider/test_views.py
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from api.models import ProviderHospitalAssignment, Hospital

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

    def test_list_only_active(self, api_client, provider_factory, user_factory):
        user = user_factory()
        api_client.force_authenticate(user=user)

        provider_factory(is_removed=False)
        provider_factory(is_removed=True)
        res = api_client.get(self.url)
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 1

    def test_search_smoke(self, api_client, provider_factory, user_factory):
        user = user_factory()
        api_client.force_authenticate(user=user)

        provider_factory(user__first_name="John", about="Cardio specialist")
        res = api_client.get(self.url, {"search": "John"})
        assert res.status_code == status.HTTP_200_OK
        print(res.data)
        assert res.data[0]["firstName"] == "John"


# ------------------------------------------------------------------
#  public sign-up  (POST /api/provider/)
# ------------------------------------------------------------------
class TestProviderSignUp:
    url = "/api/provider/"

    @pytest.fixture
    def base_payload(self):
        def _payload(**overrides):
            payload = {
                "email": "doc@test.com",
                "username": "docnew",
                "password": "Complex123!",
                "first_name": "Doc",
                "last_name": "Tor",
                "speciality": None,
                "fees": "120.00",
                "address_line1": "123 Main",
                "city": "Town",
                "state": "CA",
                "zip_code": "12345",
                "license_number": "AB123456",
            }
            payload.update(overrides)
            return payload

        return _payload

    def test_create_minimal(
        self, api_client, base_payload, speciality_factory, admin_staff_factory
    ):
        s = speciality_factory()
        a = admin_staff_factory()
        payload = base_payload(speciality=s.pk)
        api_client.force_authenticate(user=a.user)
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED, res.data
        user = User.objects.get(email="doc@test.com")
        assert hasattr(user, "provider")
        assert user.provider.fees == 120

    def test_user_create_denied(
        self, base_payload, api_client, speciality_factory, user_factory
    ):
        s = speciality_factory()
        u = user_factory()

        payload = base_payload(speciality=s.pk)
        api_client.force_authenticate(user=u)
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_speciality_required(self, base_payload, api_client, admin_staff_factory):
        a = admin_staff_factory()
        payload = base_payload()

        api_client.force_authenticate(user=a.user)
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "speciality" in res.data


# ------------------------------------------------------------------
#  onboard existing user
# ------------------------------------------------------------------
class TestProviderOnBoard:
    url = "/api/provider/onboard/"

    @pytest.fixture
    def base_payload(self):
        def _payload(**overrides):
            payload = {
                "user": None,
                "about": "test",
                "speciality": None,
                "fees": "99.99",
                "address_line1": "123 Main",
                "city": "Town",
                "state": "CA",
                "zip_code": "12345",
                "license_number": "AB123456",
            }
            payload.update(overrides)
            return payload

        return _payload

    def test_success(
        self,
        api_client,
        base_payload,
        admin_staff_factory,
        speciality_factory,
        user_factory,
    ):
        a = admin_staff_factory()
        user = user_factory()
        api_client.force_authenticate(user=a.user)
        payload = base_payload(user=user.pk, speciality=speciality_factory().pk)
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        assert hasattr(user, "provider")
        assert float(user.provider.fees) == 99.99

    def test_user_onboard_denied(
        self, base_payload, api_client, user_factory, speciality_factory
    ):
        user = user_factory()
        api_client.force_authenticate(user=user)
        payload = base_payload(speciality=speciality_factory().pk)
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_second_profile_rejected(
        self,
        base_payload,
        api_client,
        provider_factory,
        admin_staff_factory,
        speciality_factory,
    ):
        a = admin_staff_factory()
        prov = provider_factory()

        api_client.force_authenticate(user=a.user)
        payload = base_payload(user=prov.user.pk, speciality=speciality_factory().pk)
        res = api_client.post(self.url, payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        print("res: ", res.data)
        assert "already exists" in res.data["user"][0]

    def test_anonymous_denied(self, api_client):
        res = api_client.post(self.url, {}, format="json")
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


# ------------------------------------------------------------------
#  profile R / U  (GET/PATCH /api/provider/me/)
# ------------------------------------------------------------------
class TestProviderProfile:
    me_url = "/api/provider/me/"

    def test_retrieve_own(self, api_client, provider_factory):
        prov = provider_factory(about="Cardio expert")
        api_client.force_authenticate(user=prov.user)
        res = api_client.get(self.me_url)
        assert res.status_code == status.HTTP_200_OK
        assert res.data["about"] == "Cardio expert"

    def test_update_own(self, api_client, provider_factory):
        prov = provider_factory(fees=100)
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
        self, api_client, provider_factory, admin_staff_factory, hospital_factory
    ):
        h = hospital_factory()
        staff = admin_staff_factory(hospital=h)
        prov = provider_factory(primary_hospital=h, is_removed=False, removed_at=None)
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
        provider_factory,
        patient_factory,
        hospital_factory,
    ):
        h = hospital_factory()
        prov = provider_factory(primary_hospital=h, is_removed=False)
        p = patient_factory()
        api_client.force_authenticate(user=p.user)
        payload = {"is_removed": True}
        url = f"/api/provider/{prov.user.pk}/"

        res = api_client.patch(url, payload, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN

class TestProviderHospitalAffiliations:
    """Tests for provider hospital affiliation management endpoints"""
    
    def test_assign_hospital_success(
        self, provider_factory, hospital_factory, admin_staff_factory
    ):
        """Test admin can assign a hospital to a provider"""
        staff = admin_staff_factory()
        provider = provider_factory()
        hospital = hospital_factory()
        api_client = APIClient()
        
        api_client.force_authenticate(user=staff.user)
        url = f"/api/provider/{provider.user.pk}/assign_hospital/"
        
        response = api_client.post(url, {"hospital_id": hospital.id}, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["message"] == "Hospital assigned successfully"
        
        # Verify assignment was created
        provider.refresh_from_db()
        assert hospital in provider.hospitals.all()

    def test_assign_hospital_duplicate(
        self, provider_factory, hospital_factory, admin_staff_factory
    ):
        """Test assigning same hospital twice fails"""
        staff = admin_staff_factory()
        provider = provider_factory()
        hospital = hospital_factory()
        api_client = APIClient()
        
        ProviderHospitalAssignment.objects.create(
            healthcare_provider=provider,
            hospital=hospital,
            is_active=True,
            created_by=staff.user,
            updated_by=staff.user
        )
        
        api_client.force_authenticate(user=staff.user)
        url = f"/api/provider/{provider.user.pk}/assign_hospital/"
        
        response = api_client.post(url, {"hospital_id": hospital.id}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.data["error"]

    def test_assign_hospital_reactivate(
        self, provider_factory, hospital_factory, admin_staff_factory
    ):  
        staff = admin_staff_factory()
        provider = provider_factory()
        hospital = hospital_factory()
        api_client = APIClient()
        
        assignment = ProviderHospitalAssignment.objects.create(
            healthcare_provider=provider,
            hospital=hospital,
            is_active=False,
            created_by=staff.user,
            updated_by=staff.user
        )
        
        api_client.force_authenticate(user=staff.user)
        url = f"/api/provider/{provider.user.pk}/assign_hospital/"
        
        response = api_client.post(url, {"hospital_id": hospital.id}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "reactivated" in response.data["message"].lower()
        
        # Verify assignment is now active
        assignment.refresh_from_db()
        assert assignment.is_active is True

    def test_assign_hospital_not_found(
        self, provider_factory, admin_staff_factory
    ):
        """Test assigning non-existent hospital"""
        staff = admin_staff_factory()
        provider = provider_factory()
        api_client = APIClient()
        
        api_client.force_authenticate(user=staff.user)
        url = f"/api/provider/{provider.user.pk}/assign_hospital/"
        
        response = api_client.post(url, {"hospital_id": 99999}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Hospital not found" in response.data["error"]
    
    def test_unassign_hospital_success(
        self, provider_factory, hospital_factory, admin_staff_factory
    ):
        """Test admin can unassign a hospital from a provider"""
        staff = admin_staff_factory()
        provider = provider_factory()
        hospital = hospital_factory()
        api_client = APIClient()
        
        # Create active assignment
        ProviderHospitalAssignment.objects.create(
            healthcare_provider=provider,
            hospital=hospital,
            is_active=True,
            created_by=staff.user,
            updated_by=staff.user
        )
        
        api_client.force_authenticate(user=staff.user)
        url = f"/api/provider/{provider.user.pk}/unassign_hospital/"
        
        response = api_client.post(url, {"hospital_id": hospital.id}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "unassigned successfully" in response.data["message"]
        
        # Verify assignment is now inactive
        assignment = ProviderHospitalAssignment.objects.get(
            healthcare_provider=provider,
            hospital=hospital
        )
        assert assignment.is_active is False

    def test_unassign_hospital_not_active(
        self, provider_factory, hospital_factory, admin_staff_factory
    ):
        """Test unassigning a hospital that isn't actively assigned"""
        staff = admin_staff_factory()
        provider = provider_factory()
        hospital = hospital_factory()
        api_client = APIClient()
        
        # Create inactive assignment
        ProviderHospitalAssignment.objects.create(
            healthcare_provider=provider,
            hospital=hospital,
            is_active=False,
            created_by=staff.user,
            updated_by=staff.user
        )
        
        api_client.force_authenticate(user=staff.user)
        url = f"/api/provider/{provider.user.pk}/unassign_hospital/"
        
        response = api_client.post(url, {"hospital_id": hospital.id}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Active assignment not found" in response.data["error"]
    
    def test_unassign_hospital_not_assigned(
        self, provider_factory, hospital_factory, admin_staff_factory
    ):
        """Test unassigning a hospital that was never assigned"""
        staff = admin_staff_factory()
        provider = provider_factory()
        hospital = hospital_factory()
        api_client = APIClient()
        
        api_client.force_authenticate(user=staff.user)
        url = f"/api/provider/{provider.user.pk}/unassign_hospital/"
        
        response = api_client.post(url, {"hospital_id": hospital.id}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Active assignment not found" in response.data["error"]

    def test_list_hospitals(
        self, provider_factory, hospital_factory, admin_staff_factory
    ):
        """Test retrieving list of hospitals assigned to a provider"""
        staff = admin_staff_factory()
        provider = provider_factory()
        hospital1 = hospital_factory(name="General Hospital")
        hospital2 = hospital_factory(name="City Medical Center")
        api_client = APIClient()
        ProviderHospitalAssignment.objects.filter(
            healthcare_provider=provider
        ).delete()
        
        # Assign hospitals
        ProviderHospitalAssignment.objects.create(
            healthcare_provider=provider,
            hospital=hospital1,
            is_active=True,
            created_by=staff.user,
            updated_by=staff.user
        )
        ProviderHospitalAssignment.objects.create(
            healthcare_provider=provider,
            hospital=hospital2,
            is_active=True,
            created_by=staff.user,
            updated_by=staff.user
        )
        
        # Set primary hospital
        provider.primary_hospital = hospital1
        provider.save()
        
        api_client.force_authenticate(user=staff.user)
        url = f"/api/provider/{provider.user.pk}/hospitals/"
        
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        
        # Check hospital data structure
        hospital_ids = [h['id'] for h in response.data]
        assert hospital1.id in hospital_ids
        assert hospital2.id in hospital_ids
        
        # Check primary flag
        for hospital_data in response.data:
            if hospital_data['id'] == hospital1.id:
                assert hospital_data['is_primary'] is True
                assert hospital_data['name'] == "General Hospital"
            else:
                assert hospital_data['is_primary'] is False
    
    def test_list_hospitals_no_primary(
        self, provider_factory, hospital_factory, admin_staff_factory
    ):
        """Test hospitals list when no primary hospital is set"""
        staff = admin_staff_factory()
        provider = provider_factory(primary_hospital=None)
        hospital = hospital_factory()
        api_client = APIClient()
        
        ProviderHospitalAssignment.objects.create(
            healthcare_provider=provider,
            hospital=hospital,
            is_active=True,
            created_by=staff.user,
            updated_by=staff.user
        )
        
        api_client.force_authenticate(user=staff.user)
        url = f"/api/provider/{provider.user.pk}/hospitals/"
        
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['is_primary'] is False

    def test_hospital_actions_require_staff(
        self, provider_factory, hospital_factory, user_factory
    ):
        """Test that non-staff users cannot manage hospital affiliations"""
        provider = provider_factory()
        hospital = hospital_factory()
        regular_user = user_factory(is_staff=False)
        api_client = APIClient()
        
        api_client.force_authenticate(user=regular_user)
        
        # Try assign
        assign_url = f"/api/provider/{provider.user.pk}/assign_hospital/"
        response = api_client.post(assign_url, {"hospital_id": hospital.id}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Try unassign
        unassign_url = f"/api/provider/{provider.user.pk}/unassign_hospital/"
        response = api_client.post(unassign_url, {"hospital_id": hospital.id}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Try list
        list_url = f"/api/provider/{provider.user.pk}/hospitals/"
        response = api_client.get(list_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_hospital_actions_require_auth(
        self, provider_factory, hospital_factory
    ):
        """Test that unauthenticated users cannot manage hospital affiliations"""
        provider = provider_factory()
        hospital = hospital_factory()
        api_client = APIClient()
        
        # Try assign
        assign_url = f"/api/provider/{provider.user.pk}/assign_hospital/"
        response = api_client.post(assign_url, {"hospital_id": hospital.id}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Try unassign
        unassign_url = f"/api/provider/{provider.user.pk}/unassign_hospital/"
        response = api_client.post(unassign_url, {"hospital_id": hospital.id}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Try list
        list_url = f"/api/provider/{provider.user.pk}/hospitals/"
        response = api_client.get(list_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED