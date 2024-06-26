"""
Django command for waiting for the database to be ready.
"""

import time

from django.db.utils import OperationalError
from psycopg2 import OperationalError as Psycopg2Error
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        """Entry point for the management command."""
        self.stdout.write('Waiting for database...')
        db_up = False

        while db_up is False:
            try:
                self.check(databases=["default"])
                db_up = True
            except (OperationalError, Psycopg2Error):
                self.stdout.write(
                    self.style.ERROR(
                        'Database unavailable, waiting 1 second... '))
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS('Database ready!.'))
