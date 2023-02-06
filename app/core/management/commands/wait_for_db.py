"""
Django will wait to database to be ready
"""
import time

from psycopg2 import OperationalError as Psycopg2OpError

from django.core.management.base import BaseCommand
from django.db.utils import OperationalError

class Command(BaseCommand):
    """ Django Command to wait for db """

    def handle(self, *args, **options):
        self.stdout.write('Wait for database ...')
        db_up = False
        while db_up is False:
            try:
                self.check(databases=['default'])
                db_up = True
            except (Psycopg2OpError, OperationalError):
                self.stdout.write('Database unavailable, wating 1 second ...')
                time.sleep(1)
        self.stdout.write(self.style.SUCCESS('Database available!'))