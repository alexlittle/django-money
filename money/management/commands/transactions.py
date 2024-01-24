import csv

from django.core.management.base import BaseCommand

from money.models import Transaction


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('year', type=int)

    def handle(self, *args, **options):
        year = options['year']

        transactions = Transaction.objects \
            .filter(date__year=year, account_id=39) \
            .exclude(payment_type='Transfer') \
            .order_by("date")

        with open('/home/alex/Downloads/transactions.csv', 'w') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
            writer.writerow(["date",
                             "description",
                             "credit",
                             "debit"])
            for t in transactions:
                writer.writerow([t.date,
                                 t.description,
                                 t.credit,
                                 t.debit])
