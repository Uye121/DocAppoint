from pytest_factoryboy import register
import pytest
import factory

from .factories import (
    UserFactory,
    PatientFactory,
    HealthcareProviderFactory,
    HospitalFactory,
    SpecialityFactory,
    AdminStaffFactory,
    SystemAdminFactory,
)

register(UserFactory)
register(HospitalFactory)
register(SpecialityFactory)

@pytest.fixture
def provider_factory(db, user_factory):
    def make_provider(**kwargs):
        user = kwargs.pop("user", user_factory())
        return HealthcareProviderFactory(user=user, **kwargs)
    return make_provider


@pytest.fixture
def patient_factory(db, user_factory):
    def make_patient(**kwargs):
        user = kwargs.pop("user", user_factory())
        return PatientFactory(user=user, **kwargs)
    return make_patient


@pytest.fixture
def admin_staff_factory(db, user_factory):
    def make_admin_staff(**kwargs):
        user = kwargs.pop("user", user_factory())
        return AdminStaffFactory(user=user, **kwargs)
    return make_admin_staff

@pytest.fixture
def system_admin_factory(db, user_factory):
    def make_admin_staff(**kwargs):
        user = kwargs.pop("user", user_factory())
        return SystemAdminFactory(user=user, **kwargs)
    return make_admin_staff
