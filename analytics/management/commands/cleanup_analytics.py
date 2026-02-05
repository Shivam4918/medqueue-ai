from django.core.management.base import BaseCommand
from analytics.cleanup import cleanup_old_events

class Command(BaseCommand):
    help = "Delete analytics events older than retention period"

    def handle(self, *args, **kwargs):
        deleted = cleanup_old_events()
        self.stdout.write(self.style.SUCCESS(
            f"Deleted {deleted} old analytics events"
        ))
