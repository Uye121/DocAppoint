import io
import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from ...serializers import (
    AdminStaffSerializer,
    AdminStaffCreateSerializer,
    AdminStaffOnBoardSerializer,
)

User = get_user_model()

pytestmark = pytest.mark.django_db


def _dummy_image(name="1x1.png"):
    img = Image.new("RGBA", (1, 1), (255, 0, 0, 0))
    file = io.BytesIO()
    img.save(file, format="PNG")
    file.seek(0)
    return SimpleUploadedFile(name, file.read(), content_type="image/png")

class TestAdminStaffSerializer:
    def test_list(self, admin_staff_factory):
        a = admin_staff_factory()
        ss = AdminStaffSerializer(instance=a)
        data = ss.data
        assert data["user"]["id"] == str(a.user.pk)
        assert data["hospital"] == a.hospital.pk
        assert data["hospitalName"] == a.hospital.name

class TestAdminStaffCreateSerializer:
    def test_create_minimal(self, hospital_factory):
        h = hospital_factory()
        payload = {
            "email": "admin@new.com",
            "username": "adminnew",
            "password": "Complex123!",
            "first_name": "Admin",
            "last_name": "Staff",
            "hospital": h.pk,
        }
        ss = AdminStaffCreateSerializer(data=payload)
        assert ss.is_valid(), ss.errors
        obj = ss.save()
        assert obj.user.email == "admin@new.com"
        assert obj.hospital == h
        assert obj.user.check_password("Complex123!")

    def test_create_with_image(self, hospital_factory):
        h = hospital_factory()
        payload = {
            "email": "admin@img.com",
            "username": "adminimg",
            "password": "Complex123!",
            "first_name": "Pic",
            "last_name": "Ture",
            "image": _dummy_image(),
            "hospital": h.pk,
        }
        ss = AdminStaffCreateSerializer(data=payload)
        assert ss.is_valid(), ss.errors
        obj = ss.save()
        assert obj.user.image

    def test_email_case_insensitive_duplicate(self, user_factory, hospital_factory):
        user_factory(email="EXIST@example.com")
        payload = {
            "email": "exist@example.com",
            "username": "admin",
            "password": "Complex123!",
            "first_name": "A",
            "last_name": "B",
            "hospital": hospital_factory().pk,
        }
        ss = AdminStaffCreateSerializer(data=payload)
        assert not ss.is_valid()
        assert "email" in ss.errors

    def test_hospital_missing(self):
        payload = {
            "email": "admin@new.com",
            "username": "admin",
            "password": "Complex123!",
            "first_name": "A",
            "last_name": "B",
        }
        ss = AdminStaffCreateSerializer(data=payload)
        assert not ss.is_valid()
        assert "hospital" in ss.errors

class TestAdminStaffOnBoardSerializer:
    def test_create_first_time(self, rf, user_factory, hospital_factory):
        user = user_factory()
        request = rf.post("/fake/")
        request.user = user
        payload = {"hospital": hospital_factory().pk}
        ss = AdminStaffOnBoardSerializer(data=payload, context={"request": request})
        assert ss.is_valid(), ss.errors
        obj = ss.save()
        assert obj.user == user
        assert obj.hospital.pk == payload["hospital"]

    def test_second_profile_rejected(self, rf, admin_staff_factory):
        staff = admin_staff_factory()
        request = rf.post("/fake/")
        request.user = staff.user
        payload = {"hospital": staff.hospital.pk}
        ss = AdminStaffOnBoardSerializer(data=payload, context={"request": request})
        assert not ss.is_valid()
        assert "Admin staff profile already exists." in str(ss.errors)

    def test_hospital_missing(self, rf, user_factory):
        user = user_factory()
        request = rf.post("/fake/")
        request.user = user
        payload = {} 
        ss = AdminStaffOnBoardSerializer(data=payload, context={"request": request})
        assert not ss.is_valid()
        assert "hospital" in ss.errors

    def test_update_affiliation(self, rf, admin_staff_factory, hospital_factory):
        staff = admin_staff_factory()
        new_hosp = hospital_factory()
        request = rf.patch("/fake/")
        request.user = staff.user
        payload = {"hospital": new_hosp.pk}
        ss = AdminStaffOnBoardSerializer(instance=staff, data=payload, context={"request": request})
        assert ss.is_valid(), ss.errors
        obj = ss.save()
        assert obj.hospital == new_hosp