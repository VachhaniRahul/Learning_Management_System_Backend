from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Prints Hello World'

    def handle(self, *args, **kwargs):
        self.stdout.write("Hello World")

        self.stdout.write("Running makemigrations...")
        call_command('makemigrations')

        # Run migrate
        self.stdout.write("Running migrate...")
        call_command('migrate')

        self.stdout.write("Migration process completed.")