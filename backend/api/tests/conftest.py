import pytest
from pytest_factoryboy import register

from .factories import (
    UserFactory,
    PatientFactory,
    HealthcareProviderFactory,
    HospitalFactory,
    SpecialityFactory,
    AdminStaffFactory,
    SystemAdminFactory,
    MedicalRecordFactory,
    AppointmentFactory,
)

for factory in (
    UserFactory,
    PatientFactory,
    HealthcareProviderFactory,
    HospitalFactory,
    SpecialityFactory,
    AdminStaffFactory,
    SystemAdminFactory,
    MedicalRecordFactory,
    AppointmentFactory,
):
    register(factory)


@pytest.fixture
def provider_factory(healthcare_provider_factory):
    """Alias for healthcare_provider_factory"""
    return healthcare_provider_factory
