import pytest
from pytest_factoryboy import register
from rest_framework.test import APIClient

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
    SlotFactory,
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
    SlotFactory,
):
    register(factory)


@pytest.fixture
def provider_factory(healthcare_provider_factory):
    """Alias for healthcare_provider_factory"""
    return healthcare_provider_factory

@pytest.fixture
def authenticated_patient_client(patient_factory):
    def _create_patient_client(**kwargs):
        patient = patient_factory(**kwargs)
        client = APIClient()
        client.force_authenticate(user=patient.user)
        return client, patient

    return _create_patient_client

@pytest.fixture
def authenticated_provider_client(provider_factory):
    def _create_provider_client(**kwargs):
        provider = provider_factory(**kwargs)
        client = APIClient()
        client.force_authenticate(user=provider.user)
        return client, provider

    return _create_provider_client
