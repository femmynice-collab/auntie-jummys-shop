from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from shop.models import PromoCode

class Command(BaseCommand):
    help = "Seed common promo codes with schedules and limits."

    def handle(self, *args, **kwargs):
        now = timezone.now()
        seeds = [
            # code, type, value, starts, ends, usage_limit
            ("WELCOME10", "percent", Decimal("10"), now, now + timezone.timedelta(days=90), 500),
            ("FREESHIP", "amount", Decimal("5.00"), now, now + timezone.timedelta(days=30), 1000),
            ("MOVIENIGHT", "percent", Decimal("15"), now, now + timezone.timedelta(days=45), 300),
        ]
        created = 0
        for code, dtype, value, starts, ends, limit in seeds:
            obj, was_created = PromoCode.objects.get_or_create(code=code, defaults={
                "discount_type": dtype,
                "value": value,
                "active": True,
                "starts": starts,
                "ends": ends,
                "usage_limit": limit,
            })
            if not was_created:
                # Update dates/limits if already exist
                obj.discount_type = dtype
                obj.value = value
                obj.starts = starts
                obj.ends = ends
                obj.usage_limit = limit
                obj.active = True
                obj.save()
            if was_created: created += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded/updated {created} promo codes."))
