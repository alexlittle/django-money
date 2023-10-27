from django.db.models import signals
from money.models import TransactionTag, Transaction


def check_allocation_added(sender, instance, **kwargs):
    if instance.allocation_credit==0 and instance.allocation_debit==0:
        instance.allocation_credit = instance.transaction.credit
        instance.allocation_debit = instance.transaction.debit

signals.pre_save.connect(check_allocation_added, sender=TransactionTag)