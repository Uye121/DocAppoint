import io, os
import shutil
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from ...serializers import (
    SystemAdminSerializer,
    SystemAdminCreateSerializer,
    SystemAdminOnBoardSerializer,
)

User = get_user_model()

pytestmark = pytest.mark.django_db(transaction=True)

@pytest.fixture
def cleanup_images():
    """Fixture to clean up image files after test"""
    yield
    if hasattr(settings, 'TEST_MEDIA_ROOT'):
        if os.path.exists(settings.TEST_MEDIA_ROOT):
            shutil.rmtree(settings.TEST_MEDIA_ROOT, ignore_errors=True)

def _dummy_image(name="1x1.png"):
    img = Image.new("RGBA", (1, 1), (255, 0, 0, 0))
    file = io.BytesIO()
    img.save(file, format="PNG")
    file.seek(0)
    return SimpleUploadedFile(name, file.read(), content_type="image/png")

class TestSystemAdminSerializer:
    def test_list(self, system_admin_factory):
        sa = system_admin_factory()
        ser = SystemAdminSerializer(instance=sa)
        data = ser.data
        assert data["user"]["id"] == str(sa.user.pk)
        assert data["role"] == sa.role

class TestSystemAdminCreateSerializer:
    def test_create_minimal(self):
        payload = {
            "email": "sys@new.com",
            "username": "sysnew",
            "password": "Complex123!",
            "first_name": "Sys",
            "last_name": "Admin",
            "role": "super",
        }
        ser = SystemAdminCreateSerializer(data=payload)
        assert ser.is_valid(), ser.errors
        obj = ser.save()
        assert obj.user.email == "sys@new.com"
        assert obj.role == "super"
        assert obj.user.check_password("Complex123!")
        assert obj.user.is_staff

    def test_create_with_image(self):
        payload = {
            "email": "sys@img.com",
            "username": "sysimg",
            "password": "Complex123!",
            "first_name": "Pic",
            "last_name": "Ture",
            "image": _dummy_image(),
            "role": "manager",
        }
        ser = SystemAdminCreateSerializer(data=payload)
        assert ser.is_valid(), ser.errors
        obj = ser.save()
        assert obj.user.image

    def test_email_case_insensitive_duplicate(self, user_factory):
        user_factory(email="EXIST@example.com")
        payload = {
            "email": "exist@example.com",
            "username": "sys",
            "password": "Complex123!",
            "first_name": "A",
            "last_name": "B",
            "role": "super",
        }
        ser = SystemAdminCreateSerializer(data=payload)
        assert not ser.is_valid()
        assert "email" in ser.errors

    def test_role_blank_invalid(self):
        payload = {
            "email": "sys@new.com",
            "username": "sys",
            "password": "Complex123!",
            "first_name": "A",
            "last_name": "B",
            "role": "",
        }
        ser = SystemAdminCreateSerializer(data=payload)
        assert not ser.is_valid()
        assert "role" in ser.errors


    def test_role_whitespace_only_invalid(self):
        payload = {
            "email": "sys@new.com",
            "username": "sys",
            "password": "Complex123!",
            "first_name": "A",
            "last_name": "B",
            "role": "   ",
        }
        ser = SystemAdminCreateSerializer(data=payload)
        assert not ser.is_valid()
        assert "role" in ser.errors

class TestSystemAdminOnBoardSerializer:
    def test_create_first_time(self, rf, user_factory):
        user = user_factory()
        request = rf.post("/fake/")
        request.user = user
        payload = {"role": "auditor"}
        ser = SystemAdminOnBoardSerializer(data=payload, context={"request": request})
        assert ser.is_valid(), ser.errors
        obj = ser.save()
        assert obj.user == user
        assert obj.role == "auditor"

    def test_second_profile_rejected(self, rf, system_admin_factory):
        sa = system_admin_factory()
        request = rf.post("/fake/")
        request.user = sa.user
        payload = {"role": "backup"}
        ser = SystemAdminOnBoardSerializer(data=payload, context={"request": request})
        assert not ser.is_valid()
        assert "already registered as a system admin" in str(ser.errors)

    def test_role_blank(self, rf, user_factory):
        user = user_factory()
        request = rf.post("/fake/")
        request.user = user
        payload = {} 
        ser = SystemAdminOnBoardSerializer(data=payload, context={"request": request})
        assert not ser.is_valid()
        assert "role" in ser.errors

    def test_update_role(self, rf, system_admin_factory):
        sa = system_admin_factory(role="old")
        request = rf.patch("/fake/")
        request.user = sa.user
        payload = {"role": "new"}
        ser = SystemAdminOnBoardSerializer(instance=sa, data=payload, partial=True, context={"request": request})
        assert ser.is_valid(), ser.errors
        obj = ser.save()
        assert obj.role == "new"