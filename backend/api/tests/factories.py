import factory
from django.contrib.auth import get_user_model
from ..models import (
    Patient,
    HealthcareProvider,
    AdminStaff,
    SystemAdmin,
    Hospital,
    Speciality,
)

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("email",)

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@test.com")
    password = factory.django.Password("complex123!")
    first_name = "First"
    last_name = "Last"


class PatientFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Patient

    user = factory.SubFactory(UserFactory)


class SpecialityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Speciality

    name = factory.Sequence(lambda n: f"Speciality {n}")
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SelfAttribute("created_by")


class HospitalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Hospital

    name = factory.Sequence(lambda n: f"Hospital {n}")
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SelfAttribute("created_by")


class HealthcareProviderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = HealthcareProvider

    user = factory.SubFactory(UserFactory)
    speciality = factory.SubFactory(SpecialityFactory)
    fees = "100.00"
    license_number = "AB123456"
    address_line1 = "Line 1"
    city = "City"
    state = "CA"
    zip_code = "12345"
    primary_hospital = factory.SubFactory(HospitalFactory)


class AdminStaffFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AdminStaff

    user = factory.SubFactory(UserFactory)
    hospital = factory.SubFactory(HospitalFactory)


class SystemAdminFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SystemAdmin

    user = factory.SubFactory(UserFactory)
    role = "super"
