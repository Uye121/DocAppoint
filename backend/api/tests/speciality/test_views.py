import pytest
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model

from ...models import Speciality, AdminStaff
from ...views import SpecialityViewSet

User = get_user_model()

pytestmark = pytest.mark.django_db

class TestSpecialityViewSet:
    @pytest.fixture
    def viewset(self):
        return SpecialityViewSet()
    
    @pytest.fixture
    def api_factory(self):
        return APIRequestFactory()
    
    @pytest.fixture(scope='function')
    def image_file(self):
        return SimpleUploadedFile(
            "test.png", 
            b"file_content", 
            content_type="image/png"
        )
    
    @pytest.fixture
    def create_payload(self, image_file):
        def _payload(**kwargs):
            base = {
                "name": "Cardiology",
                "image": image_file,
                "description": "Heart specialist",
            }
            base.update(kwargs)
            return base
        return _payload
    
    @pytest.fixture(autouse=True)
    def cleanup(self):
        yield
        Speciality.objects.all().delete()
        AdminStaff.objects.all().delete()
        User.objects.all().delete()

class TestSpecialityPermissions(TestSpecialityViewSet):
    def test_unauthenticated_cannot_create(self, api_factory, create_payload):
        view = SpecialityViewSet.as_view({"post": "create"})
        request = api_factory.post("/specialities/", create_payload(), format="multipart")
        response = view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_regular_user_cannot_create(self, api_factory, create_payload, user_factory):
        user = user_factory()
        view = SpecialityViewSet.as_view({"post": "create"})
        request = api_factory.post("/specialities/", create_payload(), format="multipart")
        force_authenticate(request, user=user)
        response = view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_admin_can_create(self, api_factory, create_payload, admin_staff_factory):
        admin_user = admin_staff_factory()
        view = SpecialityViewSet.as_view({"post": "create"})
        request = api_factory.post("/specialities/", create_payload(), format="multipart")
        force_authenticate(request, user=admin_user.user)
        response = view(request)
        print(response.data)
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_authenticated_can_list(self, api_factory, user_factory, speciality_factory):
        speciality_factory.create_batch(3)
        user = user_factory()
        view = SpecialityViewSet.as_view({"get": "list"})
        request = api_factory.get("/specialities/")
        force_authenticate(request, user=user)
        response = view(request)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3
    
    def test_unauthenticated_cannot_list(self, api_factory):
        view = SpecialityViewSet.as_view({"get": "list"})
        request = api_factory.get("/specialities/")
        response = view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

class TestSpecialityCreate(TestSpecialityViewSet):
    
    def test_create_success(self, api_factory, create_payload, admin_staff_factory):
        admin_user = admin_staff_factory()
        payload = create_payload(name="Neurology")
        
        view = SpecialityViewSet.as_view({"post": "create"})
        request = api_factory.post("/specialities/", payload, format="multipart")
        force_authenticate(request, user=admin_user.user)
        response = view(request)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Neurology"
        assert "image" in response.data
        
        speciality = Speciality.objects.get(name="Neurology")
        assert speciality.created_by == admin_user.user
        assert speciality.updated_by == admin_user.user
        assert speciality.is_removed is False
    
    def test_create_without_image(self, api_factory, admin_staff_factory):
        admin_user = admin_staff_factory()
        payload = {
            "name": "Pediatrics",
            "description": "Child specialist",
        }
        
        view = SpecialityViewSet.as_view({"post": "create"})
        request = api_factory.post("/specialities/", payload)
        force_authenticate(request, user=admin_user.user)
        response = view(request)
        
        if response.status_code == status.HTTP_201_CREATED:
            assert Speciality.objects.filter(name="Pediatrics").exists()
        else:
            assert "image" in response.data  # Error about missing image
    
    def test_create_duplicate_name(self, api_factory, create_payload, speciality_factory, admin_staff_factory):
        speciality_factory(name="Cardiology")
        admin_user = admin_staff_factory()
        
        payload = create_payload(name="Cardiology")
        view = SpecialityViewSet.as_view({"post": "create"})
        request = api_factory.post("/specialities/", payload, format="multipart")
        force_authenticate(request, user=admin_user.user)
        response = view(request)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data
    
    def test_create_empty_name(self, api_factory, create_payload, admin_staff_factory):
        admin_user = admin_staff_factory()
        payload = create_payload(name="")
        
        view = SpecialityViewSet.as_view({"post": "create"})
        request = api_factory.post("/specialities/", payload, format="multipart")
        force_authenticate(request, user=admin_user.user)
        response = view(request)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data

class TestSpecialityRetrieve(TestSpecialityViewSet):
    
    def test_retrieve_success(self, api_factory, user_factory, speciality_factory):
        user = user_factory()
        speciality = speciality_factory(name="Cardiology")
        
        view = SpecialityViewSet.as_view({"get": "retrieve"})
        request = api_factory.get(f"/specialities/{speciality.pk}/")
        force_authenticate(request, user=user)
        response = view(request, pk=speciality.pk)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Cardiology"
        assert response.data["id"] == speciality.pk
    
    def test_retrieve_removed(self, api_factory, user_factory, speciality_factory):
        user = user_factory()
        speciality = speciality_factory(name="Removed", is_removed=True)
        
        view = SpecialityViewSet.as_view({"get": "retrieve"})
        request = api_factory.get(f"/specialities/{speciality.pk}/")
        force_authenticate(request, user=user)
        response = view(request, pk=speciality.pk)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_unauthenticated_cannot_retrieve(self, api_factory, speciality_factory):
        speciality = speciality_factory()
        
        view = SpecialityViewSet.as_view({"get": "retrieve"})
        request = api_factory.get(f"/specialities/{speciality.pk}/")
        response = view(request, pk=speciality.pk)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

class TestSpecialityUpdate(TestSpecialityViewSet):
    
    def test_update_success(self, api_factory, speciality_factory, admin_staff_factory):
        """Admin can update speciality"""
        admin_user = admin_staff_factory()
        speciality = speciality_factory(name="Old Name")
        
        payload = {
            "name": "Updated Name",
        }
        
        view = SpecialityViewSet.as_view({"patch": "partial_update"})
        request = api_factory.patch(
            f"/specialities/{speciality.pk}/", 
            payload,
            format="json"
        )
        force_authenticate(request, user=admin_user.user)
        response = view(request, pk=speciality.pk)
        
        print(response.data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Name"
        
        # Refresh from database
        speciality.refresh_from_db()
        assert speciality.name == "Updated Name"
        assert speciality.updated_by == admin_user.user
    
    def test_regular_user_cannot_update(self, api_factory, speciality_factory, user_factory):
        user = user_factory()
        speciality = speciality_factory()
        
        payload = {"name": "Hacked Name"}
        view = SpecialityViewSet.as_view({"put": "update"})
        request = api_factory.put(
            f"/specialities/{speciality.pk}/", 
            payload,
            format="json"
        )
        force_authenticate(request, user=user)
        response = view(request, pk=speciality.pk)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
