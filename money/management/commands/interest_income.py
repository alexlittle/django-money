import datetime

from django.core.management.base import BaseCommand
from django.db.models import Sum

from money.models import Transaction

START_DATE = datetime.date(2025, 4, 6)
END_DATE = datetime.date(2026, 4, 6)


class Command(BaseCommand):
    help = "Calculate interest income from given years"

    def handle(self, *args, **options):
        interest_income = (
            Transaction.objects.filter(
                date__gte=START_DATE,
                date__lt=END_DATE,
                transactiontag__tag__name="interest",
            )
            .values("account__name")
            .annotate(total=Sum("credit"))
            .order_by("account__name")
        )

        for ii in interest_income:
            print(ii["account__name"], ii["total"])
