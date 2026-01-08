import io, os
import shutil
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from ...serializers import UserSerializer

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

class TestUserSerializer:
    def test_read(self, user_factory):
        u = user_factory()
        ser = UserSerializer(instance=u)
        data = ser.data
        assert data["id"] == str(u.pk)
        assert data["email"] == u.email
        assert "password" not in data

    # ---------- CREATE ----------
    def test_create_minimal(self):
        payload = {
            "username": "neo",
            "email": "neo@example.com",
            "password": "Complex123!",
            "first_name": "Neo",
            "last_name": "Anderson",
        }
        ser = UserSerializer(data=payload)
        assert ser.is_valid(), ser.errors
        u = ser.save()
        assert u.email == "neo@example.com"
        assert u.check_password("Complex123!")
        assert not u.is_active 

    def test_create_with_image(self):
        payload = {
            "username": "img",
            "email": "img@example.com",
            "password": "Complex123!",
            "first_name": "Pic",
            "last_name": "Ture",
            "image": _dummy_image(),
        }
        ser = UserSerializer(data=payload)
        assert ser.is_valid(), ser.errors
        u = ser.save()
        assert u.image  # file stored

    def test_create_password_missing(self):
        payload = {
            "username": "nopass",
            "email": "nopass@example.com",
            "first_name": "No",
            "last_name": "Pass",
        }
        ser = UserSerializer(data=payload)
        assert not ser.is_valid()
        assert "password" in ser.errors

    def test_create_password_blank(self):
        payload = {
            "username": "blank",
            "email": "blank@example.com",
            "password": "",
            "first_name": "Blank",
            "last_name": "Pass",
        }
        ser = UserSerializer(data=payload)
        assert not ser.is_valid()
        assert "password" in ser.errors

    def test_create_email_duplicate_case_insensitive(self, user_factory):
        user_factory(email="EXIST@example.com")
        payload = {
            "username": "new",
            "email": "exist@example.com",
            "password": "Complex123!",
            "first_name": "A",
            "last_name": "B",
        }
        ser = UserSerializer(data=payload)
        assert not ser.is_valid()
        assert "email" in ser.errors

    def test_create_phone_too_long(self):
        payload = {
            "username": "longphone",
            "email": "long@example.com",
            "password": "Complex123!",
            "first_name": "A",
            "last_name": "B",
            "phone_number": "1" * 21,
        }
        ser = UserSerializer(data=payload)
        assert not ser.is_valid()
        assert "phone_number" in ser.errors

    # ---------- UPDATE ----------
    def test_update_fields(self, user_factory):
        u = user_factory()
        payload = {
            "first_name": "Updated",
            "last_name": "Name",
            "phone_number": "+123456",
        }
        ser = UserSerializer(instance=u, data=payload, partial=True)
        assert ser.is_valid(), ser.errors
        obj = ser.save()
        assert obj.first_name == "Updated"
        assert obj.last_name == "Name"
        assert obj.phone_number == "+123456"

    def test_update_password(self, user_factory):
        u = user_factory()
        old_hash = u.password
        payload = {"password": "NewComplex456!"}
        ser = UserSerializer(instance=u, data=payload, partial=True)
        assert ser.is_valid(), ser.errors
        obj = ser.save()
        assert obj.password != old_hash 
        assert obj.check_password("NewComplex456!")

    def test_update_email_duplicate(self, user_factory):
        user_factory(email="first@example.com")
        u2 = user_factory(email="second@example.com")
        payload = {"email": "FIRST@example.com"} 
        ser = UserSerializer(instance=u2, data=payload, partial=True)
        assert not ser.is_valid()
        assert "email" in ser.errors

    def test_update_phone_too_long(self, user_factory):
        u = user_factory()
        payload = {"phone_number": "1" * 21}
        ser = UserSerializer(instance=u, data=payload, partial=True)
        assert not ser.is_valid()
        assert "phone_number" in ser.errors