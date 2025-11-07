from django.core.management.base import BaseCommand
from datetime import time
from shop.models import DeliveryZone, DeliveryWindow, PickupWindow, DeliveryRate

# Expanded West Indy area ZIPs (Brownsburg, Danville, Avon, Plainfield, Speedway, Clermont, NW/SW Indy)
DEFAULT_ZIPS = [
    "46112","46122","46234","46168","46224","46254","46214","46231",
    "46113","46241","46221","46217"
]

# Store hours:
# - Mon–Thu: 11:00–20:00
# - Fri–Sat: 11:00–22:00
# - Sun:     12:00–18:00
HOURS = {
    0: (time(8,0), time(23,0)),  # Mon
    1: (time(8,0), time(23,0)),  # Tue
    2: (time(8,0), time(23,0)),  # Wed
    3: (time(8,0), time(23,0)),  # Thu
    4: (time(8,0), time(23,0)),  # Fri
    5: (time(8,0), time(23,0)),  # Sat
    6: (time(8,0), time(23,0)),  # Sun
}
class Command(BaseCommand):
    help = 'Seed delivery ZIPs and day-specific delivery windows'

    def handle(self, *args, **kwargs):
        created_zips = 0
        for z in DEFAULT_ZIPS:
            _, created = DeliveryZone.objects.get_or_create(postal_code=z)
            if created: created_zips += 1
        self.stdout.write(self.style.SUCCESS(f"Added {created_zips} ZIPs"))

        created_win = 0
        for wd, (s,e) in HOURS.items():
            _, created = DeliveryWindow.objects.get_or_create(weekday=wd, start=s, end=e)
            if created: created_win += 1
        self.stdout.write(self.style.SUCCESS(f"Added {created_win} delivery windows"))
