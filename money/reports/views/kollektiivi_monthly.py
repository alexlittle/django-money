import calendar

from datetime import datetime, timedelta

from django.conf import settings
from django.db.models import Sum, F
from django.shortcuts import render

from money.util import utils
from money.models import Account, Transaction

KOLLEKTIIVI_TAG = "kollektiivi"


def kollektiivi_balance_at_date(date):
    trans_cred = Transaction.objects \
        .filter(date__lte=date,
                transactiontag__tag__name=KOLLEKTIIVI_TAG) \
        .aggregate(credit_sum=Sum("transactiontag__allocation_credit"))
    trans_deb = Transaction.objects \
        .filter(date__lte=date,
                transactiontag__tag__name=KOLLEKTIIVI_TAG) \
        .aggregate(debit_sum=Sum("transactiontag__allocation_debit"))

    if trans_deb['debit_sum'] is None and trans_cred['credit_sum'] is None:
        return 0
    elif trans_deb['debit_sum'] is None:
        return trans_cred['credit_sum']
    elif trans_cred['credit_sum'] is None:
        return trans_deb['debit_sum']
    else:
        return trans_cred['credit_sum'] - trans_deb['debit_sum']


def kollektiivi_monthly(request, year, month):

    consulting = Transaction.objects.filter(
        date__month=month,
        date__year=year,
        transactiontag__tag__name=KOLLEKTIIVI_TAG).order_by('date')

    data = []

    for c in consulting:
        obj = {'transaction': c, 'balance': kollektiivi_balance_at_date(c.date)}
        data.append(obj)

    start_date = datetime(year, month, 1, 23, 59, 59) - timedelta(days=1)
    end_date = datetime(year, month, calendar.monthrange(year, month)[1], 23, 59, 59)

    opening_balance = kollektiivi_balance_at_date(start_date)
    closing_balance = kollektiivi_balance_at_date(end_date)

    totals = consulting.aggregate(total_credit=Sum("credit"),
                                  total_debit=Sum("debit"),
                                  total_alv_charged=Sum('sales_tax_charged'),
                                  total_alv_paid=Sum('sales_tax_paid'))

    objects = {'data': data,
               'opening_balance': opening_balance,
               'closing_balance': closing_balance,
               'start_date': datetime(year, month, 1),
               'end_date': end_date,
               'totals': totals}

    if end_date.month == datetime.now().month and end_date.year == datetime.now().year:
        objects['deposit_balance'] = utils.get_deposit_balance()
        objects['funds_available'] = closing_balance - utils.get_deposit_balance()

    return render(request, 'money/reports/kollektiivi.html', objects)
