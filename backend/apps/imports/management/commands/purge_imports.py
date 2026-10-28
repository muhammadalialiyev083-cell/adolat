from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.imports.models import ImportBatch


class Command(BaseCommand):
    help = 'Delete expired temporary import previews. Schedule at least every 15 minutes.'

    def handle(self, *args, **options):
        count, _ = ImportBatch.objects.filter(expires_at__lte=timezone.now()).delete()
        self.stdout.write(f'Expired batches removed: {count}')
