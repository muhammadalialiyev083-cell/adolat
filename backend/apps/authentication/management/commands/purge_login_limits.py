from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.authentication.models import LoginRateBucket


class Command(BaseCommand):
    help = "Delete expired login counters. Run daily; never removes active limits."

    def handle(self, *args, **options):
        count, _ = LoginRateBucket.objects.filter(expires_at__lt=timezone.now()).delete()
        self.stdout.write(f"Expired counters removed: {count}")
