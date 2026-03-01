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
def authenticated_user_client(user_factory):
    def _create_user_client(**kwargs):
        user = user_factory(**kwargs)
        client = APIClient()
        client.force_authenticate(user=user)
        return client, user

    return _create_user_client

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

@pytest.fixture
def authenticated_admin_client(admin_staff_factory):
    def _create_admin_client(**kwargs):
        admin = admin_staff_factory(**kwargs)
        client = APIClient()
        client.force_authenticate(user=admin.user)
        return client, admin

    return _create_admin_client

@pytest.fixture
def authenticated_system_admin_client(admin_staff_factory):
    def _create_system_admin_client(**kwargs):
        admin = admin_staff_factory(**kwargs)
        client = APIClient()
        client.force_authenticate(user=admin.user)
        return client, admin

    return _create_system_admin_client
