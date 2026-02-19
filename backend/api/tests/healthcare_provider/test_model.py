import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()
pytestmark = pytest.mark.django_db


class TestHealthcareProvider:
    def test_provider_positive_experience(self, provider_factory):
        with pytest.raises(IntegrityError):
            provider_factory(years_of_experience=-1)

    def test_provider_fees_positive(self, provider_factory):
        with pytest.raises(IntegrityError, match="fees_above_0"):
            provider_factory(fees=-1)

    @pytest.mark.parametrize("bad", ["abc", "12", "TOOLONGOFALICENSESTRING"])
    def test_provider_license_regex(self, provider_factory, bad):
        with pytest.raises(IntegrityError, match="valid_license_format"):
            provider_factory(license_number=bad)

    def test_valid_license_passes(self, provider_factory):
        p = provider_factory(license_number="AZ0919")
        p.validate_constraints()

    def test_primary_hospital_relation(self, provider_factory, hospital_factory):
        h = hospital_factory()
        p = provider_factory(primary_hospital=h)
        assert p.primary_hospital == h
        assert h.primary_provider.first() == p
        assert h.primary_provider.get() == p
