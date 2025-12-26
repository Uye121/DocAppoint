import json
import os
from pathlib import Path
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from api.models import Speciality, HealthcareProviderProfile, Hospital

User = get_user_model()
DOC_FILE = Path(f'{settings.MEDIA_ROOT}/doctor.json')
SPEC_FILE = Path(f'{settings.MEDIA_ROOT}/speciality.json')

class Command(BaseCommand):
    help = "Load provider data from tmp.json"

    def handle(self, *args, **options):
        if not DOC_FILE.exists() or not SPEC_FILE.exists():
            self.stdout.write(self.style.WARNING("No doctor.json nor speciality.json found – skipping seed"))
            return

        doc_data = json.loads(DOC_FILE.read_text())
        spec_data = json.loads(SPEC_FILE.read_text())

        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@docappoint.com')
        admin_password = os.environ.get('ADMIN_PASSWORD')

        admin_user, created = User.objects.get_or_create(
            email=admin_email,
            defaults={
                'username': admin_username,
                'type': User.UserType.SYSTEM_ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'first_name': 'System',
                'last_name': 'Admin'
            }
        )

        if created or not admin_user.has_usable_password():
            admin_user.set_password(admin_password)
            admin_user.save()

        # create specialities first
        for row in spec_data:
            spec, created = Speciality.objects.get_or_create(
                id=row["id"],
                defaults={
                    "name": row["name"],
                    "created_by": admin_user,
                    "updated_by": admin_user,
                }
            )

            if created:
                spec.image = row["image"]
                spec.save()

        hospital, _ = Hospital.objects.get_or_create(
            id=1,
            defaults={
                "name": "General Hospital",
                "address": "123 Main St",
                "phone_number": "555-1234",
                "timezone": "UTC",
                "created_by": admin_user,
                "updated_by": admin_user,
            }
        )

        for row in doc_data:
            firstName = row["firstName"]
            lastName = row["lastName"]
            email = f'{firstName.lower()}.{lastName.lower()}@example.com'

            try:
                user, created = User.objects.get_or_create(
                    username=f'{lastName[0].lower()}{firstName.lower()}',
                    defaults={
                        "email": email,
                        "first_name": firstName,
                        "last_name": lastName,
                        "type": User.UserType.HEALTHCARE_PROVIDER,
                    },
                )
            except IntegrityError:
                continue

            if created:
                user.set_password('doc12345')
                user.save()

            if not created and user.email != email:
                user.email = email
                user.save()

            # self.stdout.write(self.style.SUCCESS(f"Created user: {user.username}"))

            speciality = Speciality.objects.get(id=row["speciality"]["id"])

            profile, profile_created = HealthcareProviderProfile.objects.get_or_create(
                user=user,
                defaults={
                    "speciality": speciality,
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
                    "created_by": admin_user,
                    "updated_by": admin_user,
                },
            )

            if profile_created or not profile.image:
                profile.image = row["image"]
                profile.save()
            
            # attach to hospital
            profile.hospitals.add(hospital)
            
            # If this is a new profile, also set primary_hospital
            if profile_created:
                profile.primary_hospital = hospital
                profile.save()

        self.stdout.write(self.style.SUCCESS("Providers seeded"))