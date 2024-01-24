from decimal import Decimal
from django.conf import settings
from django.db.models import Sum
from money.models import InvoiceTemplate


def get_deposit_balance():
    deposit_held = InvoiceTemplate.objects.all().aggregate(total=Sum('deposit_held'))
    return Decimal(deposit_held['total'] - settings.VR_DEPOSIT)
