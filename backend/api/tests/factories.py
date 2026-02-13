import factory
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from ..models import (
    Patient,
    HealthcareProvider,
    AdminStaff,
    SystemAdmin,
    Hospital,
    Speciality,
    Appointment,
    MedicalRecord,
    ProviderHospitalAssignment,
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
        skip_postgeneration_save = True
    
    user = factory.SubFactory(UserFactory)
    speciality = factory.SubFactory(SpecialityFactory)
    fees = "100.00"
    license_number = "AB123456"
    address_line1 = "Line 1"
    city = "City"
    state = "CA"
    zip_code = "12345"
    primary_hospital = factory.SubFactory(HospitalFactory)
    
    @factory.post_generation
    def hospitals(self, create, extracted, **kwargs):
        """Post-generation hook to handle hospital affiliations"""
        if not create:
            return
        
        self.hospitals.clear()
        
        # If hospitals were passed in, use them
        if extracted:
            for hospital in extracted:
                # Create the through model with audit fields
                from api.models import ProviderHospitalAssignment
                ProviderHospitalAssignment.objects.create(
                    healthcare_provider=self,
                    hospital=hospital,
                    is_active=True,
                    created_by=self.user,
                    updated_by=self.user
                )
        # Otherwise, add the primary hospital
        elif self.primary_hospital:
            from api.models import ProviderHospitalAssignment
            ProviderHospitalAssignment.objects.create(
                healthcare_provider=self,
                hospital=self.primary_hospital,
                is_active=True,
                created_by=self.user,
                updated_by=self.user
            )

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

class AppointmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Appointment
    
    patient = factory.SubFactory(PatientFactory)
    healthcare_provider = factory.SubFactory(HealthcareProviderFactory)
    location = factory.SubFactory(HospitalFactory)

    appointment_start_datetime_utc = timezone.now() + timedelta(days=1)
    appointment_end_datetime_utc = appointment_start_datetime_utc + timedelta(minutes=30)
    
    reason = 'test'
    status = 'CONFIRMED'

class MedicalRecordFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MedicalRecord
    
    patient = factory.SubFactory(PatientFactory)
    healthcare_provider = factory.SubFactory(HealthcareProviderFactory)
    appointment = factory.SubFactory(AppointmentFactory)
    hospital = factory.SubFactory(HospitalFactory)
    diagnosis = factory.Faker('text', max_nb_chars=200)
    notes = factory.Faker('text', max_nb_chars=500)
    prescriptions = factory.Faker('text', max_nb_chars=300)
    created_by = factory.SelfAttribute('healthcare_provider.user')
    updated_by = factory.SelfAttribute('created_by')
    
    class Params:
        # Create variations easily
        removed = factory.Trait(
            is_removed=True,
            removed_at=factory.Faker('past_datetime')
        )
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Ensure the provider is affiliated with the hospital"""
        record = super()._create(model_class, *args, **kwargs)
        
        # The HealthcareProviderFactory's post_generation hook should handle this
        # But we ensure it here as well
        if not record.healthcare_provider.hospitals.filter(id=record.hospital.id).exists():
            # Create affiliation if it doesn't exist
            ProviderHospitalAssignment.objects.create(
                healthcare_provider=record.healthcare_provider,
                hospital=record.hospital,
                is_active=True,
                created_by=record.created_by,
                updated_by=record.updated_by
            )
        
        return record
