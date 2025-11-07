from django.core.management.base import BaseCommand
from shop.square_sync import pull_catalog

class Command(BaseCommand):
    help = "Pull products and variations from Square and update the local catalog."

    def handle(self, *args, **kwargs):
        created, updated = pull_catalog()
        self.stdout.write(self.style.SUCCESS(f"Square sync complete: {created} created, {updated} updated"))
