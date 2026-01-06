from pytest_factoryboy import register

from .factories import (
    UserFactory, PatientFactory, HealthcareProviderFactory,
    HospitalFactory, SpecialityFactory, AdminStaffFactory, SystemAdminFactory
)

for factory in (
    UserFactory, PatientFactory, HealthcareProviderFactory,
    HospitalFactory, SpecialityFactory, AdminStaffFactory, SystemAdminFactory
):
    register(factory)
