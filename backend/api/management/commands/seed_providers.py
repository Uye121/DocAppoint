import json
import os
from pathlib import Path
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from api.models import Speciality, HealthcareProviderProfile, Hospital

User = get_user_model()
JSON_FILE = Path("/app/tmp.json")

class Command(BaseCommand):
    help = "Load provider data from tmp.json"

    def handle(self, *args, **options):
        if not JSON_FILE.exists():
            self.stdout.write(self.style.WARNING("No tmp.json found – skipping seed"))
            return

        data = json.loads(JSON_FILE.read_text())

        admin_username = os.environ.get('ADMIN_USERNAME')
        admin_email = os.environ.get('ADMIN_EMAIL')
        admin_password = os.environ.get('ADMIN_PASSWORD')
        admin_id = int(os.environ.get('ADMIN_ID', 1))

        # Create admin user if not exist
        try:
            admin_user = User.objects.get(id=admin_id)
        except User.DoesNotExist:
            admin_user = User.objects.create_user(
                id=1,
                username=admin_username,
                email=admin_email,
                password=admin_password,
                type=User.UserType.SYSTEM_ADMIN,
                is_staff=True,
                is_superuser=True,
                first_name='System',
                last_name='Admin'
            )
            self.stdout.write(self.style.SUCCESS(f"Created admin user: {admin_user}"))

        # create specialities first
        for row in data:
            spec_row = row["speciality"]
            Speciality.objects.get_or_create(
                id=spec_row["id"],
                defaults={
                    "name": spec_row["name"],
                    "created_by": admin_user,
                    "updated_by": admin_user,
                }
            )

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

        for row in data:
            try:
                user = User.objects.get(id=row["id"])
            except User.DoesNotExist:
                user = User.objects.create_user(
                    id=row["id"],
                    username=f'doc{row["id"]}',
                    email=f'doc{row["id"]}@example.com',
                    password='doc12345',  # Set password here
                    first_name=row["firstName"],
                    last_name=row["lastName"],
                    type=User.UserType.HEALTHCARE_PROVIDER,
                    is_staff=False,
                    is_superuser=False,
                )
                self.stdout.write(self.style.SUCCESS(f"Created user: {user.username}"))

            speciality = Speciality.objects.get(id=row["speciality"]["id"])

            try:
                profile = HealthcareProviderProfile.objects.get(user=user)
                profile_created = False
            except HealthcareProviderProfile.DoesNotExist:
                # Create profile
                profile = HealthcareProviderProfile.objects.create(
                    user=user,
                    speciality=speciality,
                    education=row["degree"],
                    years_of_experience=int(float(row["experience"])),
                    about=row["about"],
                    fees=Decimal(row["fees"]),
                    address_line1=row["addressLine1"],
                    address_line2=row.get("addressLine2", ""),
                    city=row["city"],
                    state=row["state"],
                    zip_code=row["zipCode"],
                    license_number="D12345",
                    created_by=admin_user,
                    updated_by=admin_user,
                )
                profile_created = True
            
            # attach to hospital
            profile.hospitals.add(hospital)
            
            # If this is a new profile, also set primary_hospital
            if profile_created:
                profile.primary_hospital = hospital
                profile.save()

        self.stdout.write(self.style.SUCCESS("Providers seeded"))