from django.db.models import signals
from money.models import TransactionTag, Transaction


def calculate_sales_tax(sender, instance, **kwargs):
    if instance.credit > 0 and instance.sales_tax_rate > 0:
        instance.sales_tax_charged = instance.credit - (instance.credit / (1 + (instance.sales_tax_rate/100)))

def check_allocation_added(sender, instance, **kwargs):
    if instance.allocation_credit==0 and instance.allocation_debit==0:
        instance.allocation_credit = instance.transaction.credit
        instance.allocation_debit = instance.transaction.debit

signals.pre_save.connect(check_allocation_added, sender=TransactionTag)
signals.pre_save.connect(calculate_sales_tax, sender=Transaction)