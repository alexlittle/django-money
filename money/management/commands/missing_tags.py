
from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse

from money.models import Transaction


class Command(BaseCommand):
    help = 'Find transactions without tags'

    def add_arguments(self, parser):
        parser.add_argument('year', type=int)

    def handle(self, *args, **options):
        year = options['year']

        transactions = Transaction.objects \
            .filter(date__year=year, transactiontag=None) \
            .exclude(payment_type='Transfer') \
            .order_by("description")

        for t in transactions:
            print("%s - %s: %s%s" % (t.date,
                                     t.description,
                                     settings.DOMAIN_NAME,
                                     reverse('admin:money_transaction_change', args=(t.id, ))))

        print("Total: %d" % transactions.count())
