import json
import os
import environ
import mimetypes
from datetime import time, timedelta
from pathlib import Path
from decimal import Decimal
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from api.models import Speciality, Hospital, ProviderHospitalAssignment
from api.serializers import (
    HealthcareProviderCreateSerializer,
    SystemAdminCreateSerializer,
)
from ...services.appointment import generate_daily_slots

BASE_DIR = Path(__file__).resolve().parents[4]

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR / ".env"))

print(f"env: {env('PROVIDER_PASSWORD', default='failed')}")


User = get_user_model()
DOC_FILE = Path(f"{settings.MEDIA_ROOT}/doctor.json")
SPEC_FILE = Path(f"{settings.MEDIA_ROOT}/speciality.json")


def create_admin(data: dict):
    serializer = SystemAdminCreateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    provider = serializer.save()
    return provider, True


def create_provider_from_dict(data: dict):
    serializer = HealthcareProviderCreateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    provider = serializer.save()
    return provider, True


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
                spec.image = row["image"]
                spec.save()

        hospital, _ = Hospital.objects.get_or_create(
            id=1,
            defaults={
                "name": "General Hospital",
                "address_line1": "123 Main St",
                "address_line2": "",
                "phone_number": "555-1234",
                "timezone": "America/New_York",
                "created_by": admin_user,
                "updated_by": admin_user,
            },
        )

        for row in doc_data:
            first_name = row["firstName"]
            last_name = row["lastName"]
            email = f"{first_name.lower()}.{last_name.lower()}@example.com"
            username = f"{last_name[0].lower()}{first_name.lower()}"

            if User.objects.filter(email__iexact=email).exists():
                self.stdout.write(
                    self.style.WARNING(f"Skipping creating {email} – already exists")
                )
                provider = User.objects.get(email__iexact=email).provider
            else:
                with open(settings.MEDIA_ROOT / row["image"], "rb") as f:
                    image_content = f.read()

                image_name = Path(row["image"]).name
                image_type, _ = mimetypes.guess_type(image_name)
                image_type = image_type or "image/png"
                image_file = SimpleUploadedFile(
                    name=image_name, content=image_content, content_type=image_type
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

                    assigned, created = (
                        ProviderHospitalAssignment.objects.get_or_create(
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

            # Populate two weeks of slots
            today = timezone.now().date()
            for offset in range(14):
                generate_daily_slots(
                    provider=provider,
                    hospital=hospital,
                    date=today + timedelta(days=offset),
                    opening=time(9),
                    closing=time(17),
                    duration_min=30,
                )

        self.stdout.write(self.style.SUCCESS("Providers seeded"))
