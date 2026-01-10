import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model

from ...serializers import (
    SpecialitySerializer,
    SpecialityListSerializer,
    SpecialityCreateSerializer,
)
from ...models import Speciality

User = get_user_model()

pytestmark = pytest.mark.django_db(transaction=True)

class TestSpecialitySerializers:
    @pytest.fixture
    def admin_user(self, admin_staff_factory):
        return admin_staff_factory()

    @pytest.fixture
    def speciality(self, admin_user):
        return Speciality.objects.create(
            name="Cardiology",
            image=SimpleUploadedFile("c.png", b"dummy", content_type="image/png"),
            created_by=admin_user.user,
            updated_by=admin_user.user,
        )

    def test_speciality_serializer(self, speciality, admin_user):
        user = admin_user.user
        ser = SpecialitySerializer(instance=speciality)
        data = ser.data
        assert data["id"] == speciality.id
        assert data["name"] == "Cardiology"
        assert "image" in data
        assert data["isRemoved"] is False
        assert data["removedAt"] is None
        assert data["createdBy"] == user.id
        assert data["updatedBy"] == user.id

    def test_speciality_list_serializer(self, speciality):
        ser = SpecialityListSerializer(instance=speciality)
        data = ser.data
        assert set(data.keys()) == {"id", "name", "image"}
        assert data["name"] == "Cardiology"

    def test_speciality_create_serializer(self, admin_user):
        user = admin_user.user
        file = SimpleUploadedFile("n.png", b"dummy", content_type="image/png")
        payload = {"name": "Neurology", "image": file}
        ser = SpecialityCreateSerializer(data=payload)
        assert ser.is_valid(), ser.errors

        speciality = ser.save(created_by=user, updated_by=user)
        assert speciality.name == "Neurology"
        assert speciality.created_by == user
        assert speciality.updated_by == user