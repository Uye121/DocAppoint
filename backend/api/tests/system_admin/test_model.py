import uuid
import pytest
from django.db import IntegrityError
from django.contrib.auth import get_user_model

User = get_user_model()

pytestmark = pytest.mark.django_db

def test_system_admin_creation(system_admin_factory):
    s = system_admin_factory()
    assert isinstance(s.user_id, uuid.UUID)
    assert hasattr(s.user, "system_admin")
    assert s.role == "super" 

def test_system_admin_one_to_one_user(system_admin_factory, user_factory):
    u = user_factory()
    s = system_admin_factory(user=u, role="auditor")

    assert s.user == u
    assert u.system_admin == s

def test_system_admin_user_uniqueness(system_admin_factory):
    s = system_admin_factory()
    with pytest.raises(IntegrityError):
        system_admin_factory(user=s.user)
