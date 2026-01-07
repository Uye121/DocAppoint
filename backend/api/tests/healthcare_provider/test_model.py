import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator

User = get_user_model()

pytestmark = pytest.mark.django_db

class TestHealthcareProvvider:
    def test_provider_positive_experience(self, provider_factory):
        p = provider_factory.build(years_of_experience=-1)
        field = p._meta.get_field("years_of_experience")
        field.validators = [v for v in field.validators
                            if not isinstance(v, MinValueValidator)]

        with pytest.raises(ValidationError, match="experience_non_negative"):
            p.validate_constraints()

    def test_provider_fees_positive(self, provider_factory):
        p = provider_factory.build(fees=-1)
        with pytest.raises(ValidationError, match="fees_above_0"):
            p.validate_constraints()

    @pytest.mark.parametrize('bad', ['abc', '12', 'TOOLONGOFALICENSESTRING'])
    def test_provider_license_regex(self, provider_factory, bad):
        p = provider_factory.build(license_number=bad)
        with pytest.raises(ValidationError, match="valid_license_format"):
            p.validate_constraints()

    def test_valid_license_passes(self, provider_factory):
        p = provider_factory.build(license_number='AZ0919')
        p.validate_constraints() 

    def test_primary_hospital_relation(
        self,
        provider_factory,
        hospital_factory
    ):
        h = hospital_factory()
        p = provider_factory(primary_hospital=h)
        assert p.primary_hospital == h
        assert h.primary_provider.first() == p
        assert h.primary_provider.get() == p 