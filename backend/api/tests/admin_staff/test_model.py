import uuid
import pytest
from django.db import IntegrityError
from django.contrib.auth import get_user_model

User = get_user_model()

pytestmark = pytest.mark.django_db

class TestModel:
    def test_admin_staff_creation(self, admin_staff_factory):
        a = admin_staff_factory()
        assert isinstance(a.user_id, uuid.UUID) 
        assert hasattr(a.user, "admin_staff")
        assert a.hospital is not None

    def test_admin_staff_one_to_one_user(self, admin_staff_factory, user_factory):
        u = user_factory()
        a = admin_staff_factory(user=u)

        assert a.user == u
        assert u.admin_staff == a

    def test_admin_staff_hospital_relation(self, admin_staff_factory, hospital_factory):
        h = hospital_factory()
        a = admin_staff_factory(hospital=h)

        assert a.hospital == h

    def test_admin_staff_user_uniqueness(self, admin_staff_factory):
        a = admin_staff_factory()
        with pytest.raises(IntegrityError):
            admin_staff_factory(user=a.user)