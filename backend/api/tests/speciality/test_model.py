import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model

from ...models import Speciality

User = get_user_model()

pytestmark = pytest.mark.django_db(transaction=True)


class TestSpecialityModel:
    def test_create(self, admin_staff_factory):
        admin_staff = admin_staff_factory()
        obj = Speciality.objects.create(
            name="Cardiology",
            image=SimpleUploadedFile("cardio.png", b"dummy", content_type="image/png"),
            created_by=admin_staff.user,
            updated_by=admin_staff.user,
        )
        assert str(obj) == "Cardiology"
        assert obj.pk is not None
        assert not obj.is_removed
        assert obj.removed_at is None
        assert obj.is_removed is False
        assert obj.removed_at is None

    def test_unique_name(self, admin_staff_factory):
        admin_staff = admin_staff_factory()
        Speciality.objects.create(
            name="Neurology",
            image=SimpleUploadedFile("neuro.png", b"dummy", content_type="image/png"),
            created_by=admin_staff.user,
            updated_by=admin_staff.user,
        )
        with pytest.raises(Exception):
            Speciality.objects.create(
                name="Neurology",
                image=SimpleUploadedFile(
                    "neuro2.png", b"dummy", content_type="image/png"
                ),
            )
