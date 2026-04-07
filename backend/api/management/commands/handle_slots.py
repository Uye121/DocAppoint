from datetime import time, timedelta
from django.core.management.base import BaseCommand, CommandParser
from django.db import connection
from django.utils import timezone

from api.services.appointment import generate_daily_slots
from api.models import Slot, HealthcareProvider, Hospital


class Command(BaseCommand):
    help = "Manage appointment slots: purge old free slots and generate new ones"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--generate",
            action="store_true",
            help="Generate new slots for the next n days",
        )
        parser.add_argument(
            "--purge",
            action="store_true",
            help="Purge old free slots from previous weeks",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=14,
            help="Number of days to purge/generate (default: 14)",
        )

    def handle(self, *args, **options):
        days = options["days"]

        if options["purge"]:
            self.purge_old_slots(days=days)

        if options["generate"]:
            self.generate_new_slots(days=days)

    def purge_old_slots(self, days: int = 14) -> None:
        """
        Remove FREE slots older than n days ago.

        Args:
            days: Number of days to look back (default: 14)
        """
        table = Slot._meta.db_table

        with connection.cursor() as c:
            c.execute(
                f'DELETE FROM "{table}" WHERE start < CURRENT_DATE - INTERVAL %s AND status = %s',
                [f"{days} days", Slot.Status.FREE],
            )
            rows_deleted = c.rowcount
        self.stdout.write(self.style.SUCCESS(f"Purged {rows_deleted} old free slots"))

    def generate_new_slots(self, days: int = 14) -> None:
        """
        Generate new FREE slots for all providers for the next n days.

        Args:
            days: Number of days to generate slots for (default: 14)
        """
        today = timezone.now().date()

        providers = HealthcareProvider.objects.filter(is_removed=False)

        if not providers.exists():
            self.stdout.write(self.style.WARNING("No active providers found"))
            return

        hospital = Hospital.objects.first()
        if not hospital:
            self.stdout.write(self.style.ERROR("No hospital found"))
            return

        self.stdout.write(
            f"Generating slots for {providers.count()} providers for {days} days..."
        )

        for provider in providers:
            for offset in range(days):
                date = today + timedelta(days=offset)
                generate_daily_slots(
                    provider=provider,
                    hospital=hospital,
                    date=date,
                    duration_min=30,
                    opening=time(9, 0),
                    closing=time(17, 0),
                )

        self.stdout.write(self.style.SUCCESS("Successfully generated free slots."))
