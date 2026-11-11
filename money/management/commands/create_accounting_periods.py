import datetime

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from money.models import AccountingPeriod

# (start month, start day, end month, end day)
QUARTERS = [
    (1, 1, 3, 31),
    (4, 1, 6, 30),
    (7, 1, 9, 30),
    (10, 1, 12, 31),
]


class Command(BaseCommand):
    help = "Create the four quarterly accounting periods for the given year"

    def add_arguments(self, parser):
        parser.add_argument("year", type=int, help="The year to create accounting periods for")

    def handle(self, *args, **options):
        year = options["year"]
        if not 1900 <= year <= 2200:
            raise CommandError(f"Invalid year: {year}")

        for i, (start_month, start_day, end_month, end_day) in enumerate(QUARTERS, start=1):
            start = timezone.make_aware(datetime.datetime(year, start_month, start_day, 0, 0, 0))
            end = timezone.make_aware(datetime.datetime(year, end_month, end_day, 23, 59, 59))
            title = f"{year} Q{i}"

            _, created = AccountingPeriod.objects.get_or_create(
                start_date=start,
                end_date=end,
                defaults={"title": title, "active": True},
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created {title}"))
            else:
                self.stdout.write(f"Skipped {title} (already exists)")
