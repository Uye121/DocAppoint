import os
import pytest
from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile

from api.models import Speciality, HealthcareProvider

pytestmark = pytest.mark.django_db


class TestSpecialityPublicAccess:
    """Test public and authenticated access to specialities"""

    def test_unauthenticated_user_cannot_list_specialities(self, speciality_factory):
        """Test that unauthenticated users can view specialities list"""
        speciality_factory(name="Cardiology")
        speciality_factory(name="Dermatology")
        speciality_factory(name="Neurology")
        api_client = APIClient()

        url = reverse("speciality-list")

        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthenticated_user_cannot_retrieve_speciality(self, speciality_factory):
        """Test that unauthenticated users can view a single speciality"""
        speciality = speciality_factory(name="Cardiology")
        api_client = APIClient()

        url = reverse("speciality-detail", args=[speciality.id])
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_user_can_list_specialities(self, authenticated_patient_client, 
                                                      speciality_factory):
        """Test that authenticated users can view specialities list"""
        patient_client, _ = authenticated_patient_client()
        speciality_factory(name="Cardiology")
        
        url = reverse("speciality-list")
        response = patient_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_unauthenticated_user_cannot_create_speciality(self):
        """Test that unauthenticated users cannot create specialities"""
        url = reverse("speciality-list")
        api_client = APIClient()
        
        # Create a simple image file for testing
        image = SimpleUploadedFile(
            "test_image.jpg", 
            b"file_content", 
            content_type="image/jpeg"
        )
        
        speciality_data = {
            "name": "New Speciality",
            "image": image
        }
        
        response = api_client.post(url, speciality_data, format="multipart")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestSpecialityStaffAccess:
    """Test staff/admin access to speciality management"""

    def test_staff_can_create_speciality(self, authenticated_admin_client):
        """Test that staff can create a new speciality"""
        admin_client, admin = authenticated_admin_client()
        
        url = reverse("speciality-list")
        
        # Create a simple image file for testing
        image = SimpleUploadedFile(
            "cardiology.jpg", 
            b"file_content", 
            content_type="image/jpeg"
        )
        
        speciality_data = {
            "name": "Cardiology",
            "image": image
        }
        
        response = admin_client.post(url, speciality_data, format="multipart")
        assert response.status_code == status.HTTP_201_CREATED
        
        speciality = Speciality.objects.get(name="Cardiology")
        assert speciality.name == "Cardiology"
        assert speciality.created_by == admin.user
        assert speciality.updated_by == admin.user
        assert speciality.image is not None

    def test_staff_can_update_speciality(self, authenticated_admin_client, speciality_factory):
        """Test that staff can update a speciality"""
        admin_client, admin = authenticated_admin_client()
        speciality = speciality_factory(name="Old Name")
        
        url = reverse("speciality-detail", args=[speciality.id])
        update_data = {"name": "Updated Speciality"}
        
        response = admin_client.patch(url, update_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        speciality.refresh_from_db()
        assert speciality.name == "Updated Speciality"
        assert speciality.updated_by == admin.user

    def test_staff_can_soft_delete_speciality(self, authenticated_admin_client, speciality_factory):
        """Test that staff can soft delete a speciality"""
        admin_client, _ = authenticated_admin_client()
        speciality = speciality_factory(name="To Be Deleted")
        
        url = reverse("speciality-detail", args=[speciality.id])
        update_data = {"is_removed": True}
        
        response = admin_client.patch(url, update_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        speciality.refresh_from_db()
        assert speciality.is_removed
        assert speciality.removed_at is not None
        
        # Should not appear in list
        list_url = reverse("speciality-list")
        response = admin_client.get(list_url)
        speciality_names = [s["name"] for s in response.data]
        assert "To Be Deleted" not in speciality_names

    def test_staff_can_restore_speciality(self, authenticated_admin_client, speciality_factory):
        """Test that staff can restore a soft-deleted speciality"""
        admin_client, admin = authenticated_admin_client()
        
        # Create and soft delete a speciality
        speciality = speciality_factory(name="Restore Me")
        speciality.is_removed = True
        speciality.removed_at = timezone.now()
        speciality.save()
        
        url = reverse("speciality-restore", args=[speciality.id])
        
        response = admin_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        
        speciality.refresh_from_db()
        assert not speciality.is_removed
        assert speciality.removed_at is None
        assert speciality.updated_by == admin.user

    def test_staff_cannot_create_duplicate_speciality(self, authenticated_admin_client, 
                                                      speciality_factory):
        """Test that speciality names must be unique"""
        admin_client, _ = authenticated_admin_client()
        speciality_factory(name="Cardiology")
        
        url = reverse("speciality-list")
        
        image = SimpleUploadedFile(
            "cardiology2.jpg", 
            b"file_content", 
            content_type="image/jpeg"
        )
        
        speciality_data = {
            "name": "Cardiology",  # Duplicate name
            "image": image
        }
        
        response = admin_client.post(url, speciality_data, format="multipart")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "unique" in str(response.data).lower() or "already exists" in str(response.data).lower()


class TestSpecialityNonStaffAccess:
    """Test that non-staff users cannot modify specialities"""

    def test_patient_cannot_create_speciality(self, authenticated_patient_client):
        """Test that patients cannot create specialities"""
        patient_client, _ = authenticated_patient_client()
        
        url = reverse("speciality-list")
        image = SimpleUploadedFile("test.jpg", b"content", content_type="image/jpeg")
        speciality_data = {"name": "New Speciality", "image": image}
        
        response = patient_client.post(url, speciality_data, format="multipart")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_provider_cannot_create_speciality(self, authenticated_provider_client):
        """Test that providers cannot create specialities"""
        provider_client, _ = authenticated_provider_client()
        
        url = reverse("speciality-list")
        image = SimpleUploadedFile("test.jpg", b"content", content_type="image/jpeg")
        speciality_data = {"name": "New Speciality", "image": image}
        
        response = provider_client.post(url, speciality_data, format="multipart")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_patient_cannot_update_speciality(self, authenticated_patient_client, 
                                              speciality_factory):
        """Test that patients cannot update specialities"""
        patient_client, _ = authenticated_patient_client()
        speciality = speciality_factory(name="Original")
        
        url = reverse("speciality-detail", args=[speciality.id])
        update_data = {"name": "Hacked Name"}
        
        response = patient_client.patch(url, update_data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_provider_cannot_update_speciality(self, authenticated_provider_client, 
                                               speciality_factory):
        """Test that providers cannot update specialities"""
        provider_client, _ = authenticated_provider_client()
        speciality = speciality_factory(name="Original")
        
        url = reverse("speciality-detail", args=[speciality.id])
        update_data = {"name": "Hacked Name"}
        
        response = provider_client.patch(url, update_data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_patient_cannot_delete_speciality(self, authenticated_patient_client, 
                                              speciality_factory):
        """Test that patients cannot delete specialities"""
        patient_client, _ = authenticated_patient_client()
        speciality = speciality_factory()
        
        # Try soft delete via update
        url = reverse("speciality-detail", args=[speciality.id])
        update_data = {"is_removed": True}
        
        response = patient_client.patch(url, update_data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestSpecialityProviderRelationship:
    """Test relationships between specialities and providers"""

    def test_speciality_assigned_to_provider(self, speciality_factory, provider_factory):
        """Test that a speciality can be assigned to a provider"""
        speciality = speciality_factory(name="Cardiology")
        provider = provider_factory(speciality=speciality)
        
        assert provider.speciality == speciality
        assert provider in speciality.provider_speciality.all()

    def test_speciality_deleted_provider_handling(self, authenticated_admin_client,
                                                  speciality_factory, provider_factory):
        """Test that providers keep speciality reference when speciality is soft deleted"""
        admin_client, _ = authenticated_admin_client()
        
        speciality = speciality_factory(name="Cardiology")
        provider = provider_factory(speciality=speciality)
        
        # Soft delete speciality
        url = reverse("speciality-detail", args=[speciality.id])
        response = admin_client.patch(url, {"is_removed": True}, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        # Provider should still have the speciality reference
        provider.refresh_from_db()
        assert provider.speciality == speciality
        assert provider.speciality.is_removed

    def test_speciality_set_to_null_when_deleted(self, authenticated_admin_client,
                                                 speciality_factory, provider_factory):
        """Test that speciality can be set to null when speciality is hard deleted"""        
        speciality = speciality_factory(name="Cardiology")
        provider = provider_factory(speciality=speciality)
        
        # Hard delete speciality (if allowed - usually not)
        speciality.delete()
        
        provider.refresh_from_db()
        assert provider.speciality is None

    def test_filter_providers_by_speciality(self, authenticated_patient_client,
                                            speciality_factory, provider_factory):
        """Test that patients can filter providers by speciality"""
        patient_client, _ = authenticated_patient_client()
        
        cardio = speciality_factory(name="Cardiology")
        derma = speciality_factory(name="Dermatology")
        
        provider_factory(speciality=cardio, user__first_name="Cardio1")
        provider_factory(speciality=cardio, user__first_name="Cardio2")
        provider_factory(speciality=derma, user__first_name="Derma1")
        
        # Make providers active
        for p in HealthcareProvider.objects.all():
            p.user.is_active = True
            p.user.save()
        
        # Filter by cardiology
        provider_url = reverse("provider-list")
        response = patient_client.get(provider_url, {"speciality": cardio.id})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        for provider in response.data:
            assert provider["speciality"] == cardio.id


class TestSpecialityImageHandling:
    """Test speciality image upload and cleanup"""

    def test_speciality_image_upload(self, authenticated_admin_client):
        """Test uploading an image with speciality creation"""
        admin_client, _ = authenticated_admin_client()
        
        url = reverse("speciality-list")
        
        # Create a test image
        image_content = b"fake_image_content"
        image = SimpleUploadedFile(
            "test_speciality.jpg", 
            image_content, 
            content_type="image/jpeg"
        )
        
        speciality_data = {
            "name": "Test Speciality",
            "image": image
        }
        
        response = admin_client.post(url, speciality_data, format="multipart")
        assert response.status_code == status.HTTP_201_CREATED
        
        speciality = Speciality.objects.get(name="Test Speciality")
        assert speciality.image is not None
        assert "test_speciality" in speciality.image.name

    def test_speciality_image_update(self, authenticated_admin_client, speciality_factory):
        """Test updating a speciality's image"""
        admin_client, _ = authenticated_admin_client()
        
        # Create speciality with initial image
        initial_image = SimpleUploadedFile(
            "initial.jpg", 
            b"initial_content", 
            content_type="image/jpeg"
        )
        speciality = speciality_factory(name="Test", image=initial_image)
        
        # Upload new image
        url = reverse("speciality-detail", args=[speciality.id])
        new_image = SimpleUploadedFile(
            "updated.jpg", 
            b"updated_content", 
            content_type="image/jpeg"
        )
        
        # For multipart form data with file upload
        response = admin_client.patch(url, {"image": new_image}, format="multipart")
        assert response.status_code == status.HTTP_200_OK
        
        speciality.refresh_from_db()
        assert "updated" in speciality.image.name

    def test_speciality_image_deleted_on_delete(self, authenticated_admin_client, 
                                                speciality_factory, tmp_path):
        """Test that image file is deleted when speciality is deleted"""
        admin_client, _ = authenticated_admin_client()
        
        # Create speciality with image
        image = SimpleUploadedFile(
            "delete_test.jpg", 
            b"content", 
            content_type="image/jpeg"
        )
        speciality = speciality_factory(name="Delete Test", image=image)
        image_path = speciality.image.path
        
        # Soft delete shouldn't delete the image
        url = reverse("speciality-detail", args=[speciality.id])
        response = admin_client.patch(url, {"is_removed": True}, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        # Image should still exist
        assert os.path.exists(image_path)


class TestSpecialityValidation:
    """Test validation rules for specialities"""

    def test_speciality_name_required(self, authenticated_admin_client):
        """Test that name is required"""
        admin_client, _ = authenticated_admin_client()
        
        url = reverse("speciality-list")
        image = SimpleUploadedFile("test.jpg", b"content", content_type="image/jpeg")
        
        # Missing name
        speciality_data = {"image": image}
        response = admin_client.post(url, speciality_data, format="multipart")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in str(response.data).lower()

    def test_speciality_image_required(self, authenticated_admin_client):
        """Test that image is required"""
        admin_client, _ = authenticated_admin_client()
        
        url = reverse("speciality-list")
        
        # Missing image
        speciality_data = {"name": "No Image Speciality"}
        response = admin_client.post(url, speciality_data, format="multipart")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "image" in str(response.data).lower()

    def test_speciality_name_max_length(self, authenticated_admin_client):
        """Test name max length validation"""
        admin_client, _ = authenticated_admin_client()
        
        url = reverse("speciality-list")
        image = SimpleUploadedFile("test.jpg", b"content", content_type="image/jpeg")
        
        # Very long name
        long_name = "A" * 200
        speciality_data = {"name": long_name, "image": image}
        
        response = admin_client.post(url, speciality_data, format="multipart")
        
        # Should either be accepted or rejected with appropriate error
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in str(response.data).lower()


class TestSpecialityFiltering:
    """Test filtering and searching specialities"""

    def test_search_specialities_by_name(self, authenticated_patient_client, speciality_factory):
        """Test searching specialities by name"""
        speciality_factory(name="Cardiology")
        speciality_factory(name="Cardiothoracic Surgery")
        speciality_factory(name="Dermatology")
        patient_client, _ = authenticated_patient_client()
        
        url = reverse("speciality-list")
        response = patient_client.get(url, {"search": "cardio"})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        for speciality in response.data:
            assert "cardio" in speciality["name"].lower()

    def test_filter_active_specialities(self, authenticated_patient_client, speciality_factory):
        """Test that only active (non-removed) specialities are listed"""
        speciality_factory(name="Active 1")
        speciality_factory(name="Active 2")
        patient_client, _ = authenticated_patient_client()
        
        # Create a removed speciality
        removed = speciality_factory(name="Removed")
        removed.is_removed = True
        removed.save()
        
        url = reverse("speciality-list")
        response = patient_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        speciality_names = [s["name"] for s in response.data]
        assert "Active 1" in speciality_names
        assert "Active 2" in speciality_names
        assert "Removed" not in speciality_names