from typing import Optional
import json
import mimetypes
from pathlib import Path
from decimal import Decimal
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from api.models import (
    Speciality,
    Hospital,
    Patient,
    HealthcareProvider,
    AdminStaff,
    ProviderHospitalAssignment,
)
from api.serializers import (
    PatientCreateSerializer,
    HealthcareProviderCreateSerializer,
    SystemAdminCreateSerializer,
)
from api.utils.env import env


User = get_user_model()
DOC_FILE = Path(settings.FIXTURES_DIR) / "doctor.json"
SPEC_FILE = Path(settings.FIXTURES_DIR) / "speciality.json"


def create_admin(data: dict) -> tuple[AdminStaff, bool]:
    """
    Create a new system administrator user.

    Args:
        data (dict): Dictionary containing admin creation fields.

    Returns:
        tuple[AdminStaff, bool]: A tuple containing:
            - AdminStaff: The newly created admin user instance
            - bool: True if the admin was newly created
    """
    serializer = SystemAdminCreateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    admin = serializer.save()
    return admin, True


def create_provider_from_dict(data: dict) -> tuple[HealthcareProvider, bool]:
    """
    Create a new provider user.

    Args:
        data (dict): Dictionary containing provider creation fields.

    Returns:
        tuple[HealthcareProvider, bool]: A tuple containing:
            - HealthcareProvider: The newly created provider user instance
            - bool: True if the admin was newly created
    """
    serializer = HealthcareProviderCreateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    provider = serializer.save()
    return provider, True


def create_patient_from_dict(data: dict) -> tuple[Patient, bool]:
    """
    Create a new patient user.

    Args:
        data (dict): Dictionary containing patient creation fields.

    Returns:
        tuple[Patient, bool]: A tuple containing:
            - Patient: The newly created patient user instance
            - bool: True if the admin was newly created
    """
    serializer = PatientCreateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    patient = serializer.save()
    return patient, True


def get_uploaded_file_from_fixture(fixture_path) -> Optional[SimpleUploadedFile]:
    """
    Prepare an image from fixtures as SimpleUploadedFile.

    Args:
        fixture_path (string): Path to the fixture file

    Returns:
        SimpleUploadedFile or None: Ready to assign to FileField/ImageField
    """
    source = settings.FIXTURES_DIR / fixture_path

    if not source.exists():
        return None

    with open(source, "rb") as f:
        file_content = f.read()

    file_name = Path(fixture_path).name
    content_type, _ = mimetypes.guess_type(file_name)
    content_type = content_type or "application/octet-stream"

    return SimpleUploadedFile(
        name=file_name, content=file_content, content_type=content_type
    )


class Command(BaseCommand):
    help = "Load provider data from tmp.json"

    def handle(self, *args, **options):
        if not DOC_FILE.exists() or not SPEC_FILE.exists():
            self.stdout.write(
                self.style.WARNING(
                    "No doctor.json nor speciality.json found – skipping seed"
                )
            )
            return

        doc_data = json.loads(DOC_FILE.read_text())
        spec_data = json.loads(SPEC_FILE.read_text())

        self.stdout.write(self.style.NOTICE("Seeding application..."))

        # Try to create admin user
        admin_username = env.str("ADMIN_USERNAME", default="admin")
        admin_email = env.str("ADMIN_EMAIL", default="admin@docappoint.com")
        admin_password = env.str("ADMIN_PASSWORD")
        payload = {
            "email": admin_email,
            "username": admin_username,
            "password": admin_password,
            "first_name": "System",
            "last_name": "Admin",
            "role": "Software Engineer",
        }

        try:
            admin_user, created = create_admin(payload)
            if created or not admin_user.has_usable_password():
                User.objects.filter(pk=admin_user.user_id).update(
                    is_active=True,
                )
                admin_user.set_password(admin_password)
                admin_user.save()
        except Exception:
            self.stdout.write(self.style.WARNING("System admin already created"))
            admin_user = User.objects.get(email=admin_email, username=admin_username)

        # Create test patient user
        payload = {
            "email": "jdoe@abc.com",
            "username": "jdoe",
            "password": env.str("TEST_PATIENT_PASSWORD"),
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-01",
            "blood_type": "O+",
            "allergies": "None",
            "chronic_conditions": "None",
            "current_medications": "None",
            "insurance": "Test Insurance",
            "weight": 70,
            "height": 175,
        }

        try:
            patient, created = create_patient_from_dict(payload)
            if created:
                patient.user.is_active = True
                patient.user.save()
        except Exception:
            self.stdout.write(self.style.WARNING("Patient user already created"))

        # create specialities first
        for row in spec_data:
            spec, created = Speciality.objects.get_or_create(
                id=row["id"],
                defaults={
                    "name": row["name"],
                    "created_by": admin_user,
                    "updated_by": admin_user,
                },
            )

            if created:
                image_file = get_uploaded_file_from_fixture(row["image"])

                if image_file:
                    spec.image = image_file
                    spec.save()
                    self.stdout.write(
                        self.style.SUCCESS(f"Created speciality {spec.name} with image")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Image not found for speciality {spec.name}: {row['image']}"
                        )
                    )

        hospital, _ = Hospital.objects.get_or_create(
            id=1,
            defaults={
                "name": "General Hospital",
                "address_line1": "123 Main St",
                "address_line2": "",
                "city": "Queens",
                "state": "NY",
                "zip_code": "10001",
                "phone_number": "555-1234",
                "timezone": "America/New_York",
                "created_by": admin_user,
                "updated_by": admin_user,
            },
        )

        # Create providers if they do not exist already
        for row in doc_data:
            first_name = row["firstName"]
            last_name = row["lastName"]
            email = f"{first_name.lower()}.{last_name.lower()}@example.com"
            username = f"{last_name[0].lower()}{first_name.lower()}"

            # Create user if not exist
            if User.objects.filter(email__iexact=email).exists():
                self.stdout.write(
                    self.style.WARNING(f"Skip creating {email} – already exists")
                )
                provider = User.objects.get(email__iexact=email).provider
            else:
                image_file = get_uploaded_file_from_fixture(row["image"])

                if not image_file:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Image not found for {first_name} {last_name}: {row['image']}"
                        )
                    )

                payload = {
                    "email": email,
                    "username": username,
                    "password": env("PROVIDER_PASSWORD", default="doc12345"),
                    "first_name": first_name,
                    "last_name": last_name,
                    "date_of_birth": None,
                    "speciality": row["speciality"]["id"],
                    "education": row["degree"],
                    "years_of_experience": int(float(row["experience"])),
                    "about": row["about"],
                    "fees": Decimal(row["fees"]),
                    "address_line1": row["addressLine1"],
                    "address_line2": row.get("addressLine2", ""),
                    "city": row["city"],
                    "state": row["state"],
                    "zip_code": row["zipCode"],
                    "license_number": "D12345",
                    "image": image_file,
                }

                try:
                    provider, created = create_provider_from_dict(payload)
                except ValidationError as e:
                    self.stdout.write(
                        self.style.WARNING(f"Skipping {email}: {e.detail}")
                    )
                    continue

                # If this is a new profile, also set primary_hospital
                if created:
                    provider.primary_hospital = hospital
                    provider.save(update_fields=["primary_hospital"])
                    provider.user.is_active = True
                    provider.user.save(update_fields=["is_active"])

                    _, created = ProviderHospitalAssignment.objects.get_or_create(
                        healthcare_provider=provider,
                        hospital=hospital,
                        defaults={
                            "is_active": True,
                            "start_datetime_utc": timezone.now(),
                            "end_datetime_utc": None,
                            "created_by": admin_user,
                            "updated_by": admin_user,
                        },
                    )

                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(f"Assigned {provider} to {hospital}")
                        )

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"{'Created' if created else 'Existed'}: {provider}"
                        )
                    )

        self.stdout.write(self.style.SUCCESS("Providers seeded"))
