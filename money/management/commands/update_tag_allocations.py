from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse
from django.db.models import Count
from money.models import Transaction, Tag, TransactionTag


class Command(BaseCommand):
    help = 'Find transactions with missing allocations'

    def handle(self, *args, **options):
        transaction_tags = TransactionTag.objects.filter(allocation_credit=0, allocation_debit=0)

        for tt in transaction_tags:
            print(tt.transaction.description)
            # if only 1 tag for the transaction then auto-update the values
            transaction = Transaction.objects.filter(pk=tt.transaction.id).annotate(count_tags=Count("transactiontag")).first()
            if transaction.count_tags == 1:
                tt.allocation_credit = transaction.credit
                tt.allocation_debit = transaction.debit
                tt.save()
            else:
                print("Edit: %s%s" % ("http://localhost:8000", reverse("admin:money_transaction_change", args=[transaction.id])))
