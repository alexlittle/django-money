import datetime
import dateutil.relativedelta

from django.conf import settings
from django.db.models import Sum, Max
from django.shortcuts import render
from django.template import RequestContext
from django.utils import timezone

from money.models import Account, Transaction, Valuation, RegularPayment, \
    ExchangeRate


def consulting_quarters(request, quarter):
    CONSULTING_ID = 47
    CONSULTING_EXTRAS_ID = 49

    QUARTERS = {
                '2019-4': 
                    {'start_date': datetime.datetime(2019, 10, 1, 0, 0, 0),
                     'end_date': datetime.datetime(2019, 12, 31, 23, 59, 59)},
                '2020-1':
                    {'start_date': datetime.datetime(2020, 1, 1, 0, 0, 0),
                     'end_date': datetime.datetime(2020, 3, 31, 23, 59, 59)},
                '2020-2':
                    {'start_date': datetime.datetime(2020, 4, 1, 0, 0, 0),
                     'end_date': datetime.datetime(2020, 6, 30, 23, 59, 59)},
                '2020-3':
                    {'start_date': datetime.datetime(2020, 7, 1, 0, 0, 0),
                     'end_date': datetime.datetime(2020, 9, 30, 23, 59, 59)},
                '2020-4':
                    {'start_date': datetime.datetime(2020, 10, 1, 0, 0, 0),
                     'end_date': datetime.datetime(2020, 12, 31, 23, 59, 59)},
                '2021-1':
                    {'start_date': datetime.datetime(2021, 1, 1, 0, 0, 0),
                     'end_date': datetime.datetime(2021, 3, 31, 23, 59, 59)},
                '2021-2':
                    {'start_date': datetime.datetime(2021, 4, 1, 0, 0, 0),
                     'end_date': datetime.datetime(2021, 6, 30, 23, 59, 59)},
                '2021-3':
                    {'start_date': datetime.datetime(2021, 7, 1, 0, 0, 0),
                     'end_date': datetime.datetime(2021, 9, 30, 23, 59, 59)},
                '2021-4':
                    {'start_date': datetime.datetime(2021, 10, 1, 0, 0, 0),
                     'end_date': datetime.datetime(2021, 12, 31, 23, 59, 59)},
                }

    START_DATE = QUARTERS[quarter]['start_date']
    END_DATE = QUARTERS[quarter]['end_date']

    consulting_account = Account.objects.get(pk=CONSULTING_ID)
    consulting = Transaction.objects.filter(
        account_id=CONSULTING_ID,
        date__gte=START_DATE,
        date__lte=END_DATE).order_by('date')

    data = []
    for c in consulting:
        obj = {'transaction': c,
               'balance': Account.get_balance_base_currency_at_date(
            c.account, c.date)}
        if c.debit != 0 and c.sales_tax_paid != 0:
            obj['ex_sales_tax'] = c.debit - c.sales_tax_paid
        data.append(obj)

    opening_balance = Account.get_balance_base_currency_at_date(
        consulting_account, START_DATE)
    closing_balance = Account.get_balance_base_currency_at_date(
        consulting_account, END_DATE)

    consulting_extras = Transaction.objects.filter(
        account_id=CONSULTING_EXTRAS_ID,
        date__gte=START_DATE, date__lte=END_DATE).order_by('date')

    return render(request, 'money/reports/consulting_quarter.html',
                  {'data': data,
                   'opening_balance': opening_balance,
                   'closing_balance': closing_balance,
                   'start_date': START_DATE,
                   'end_date': END_DATE,
                   'consulting_extras': consulting_extras})