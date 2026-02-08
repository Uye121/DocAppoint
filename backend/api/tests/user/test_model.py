import uuid
import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()
pytestmark = pytest.mark.django_db


def test_user_pk_is_uuid(user_factory):
    u = user_factory()
    assert isinstance(u.pk, uuid.UUID)


def test_email_case_insensitive_unique(user_factory):
    user_factory(email="Alice@Test.com")
    with pytest.raises(ValidationError):
        User.objects.create_user(
            username="bob", email="alice@test.com", first_name="Bob", last_name="Marley"
        )


def test_email_used_as_username():
    assert User.USERNAME_FIELD == "email"


def test_required_fields():
    assert "username" in User.REQUIRED_FIELDS


def test_first_and_last_name_not_blank():
    with pytest.raises(ValidationError):
        User.objects.create(username="x", email="x@y.com", first_name="", last_name="Y")

    with pytest.raises(ValidationError):
        User.objects.create(username="x", email="x@y.com", first_name="X", last_name="")
