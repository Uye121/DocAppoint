from django.core.management.base import BaseCommand
from django.db import connection

from api.models import Slot

class Command(BaseCommand):
    help = "Delete appointment slots older than the current ISO week"
    table = Slot._meta.db_table

    def handle(self, *args, **options):
        with connection.cursor() as c:
            c.execute(f'DELETE FROM "{self.table}" WHERE start < date_trunc(%s, CURRENT_DATE)', ['week'])
        self.stdout.write(self.style.SUCCESS("Purged old slots"))
