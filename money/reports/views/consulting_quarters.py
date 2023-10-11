import datetime

from django.shortcuts import render

from money.models import Account, Transaction

from money import lib


def consulting_quarters(request, quarter):
    CONSULTING_ID = 47
    CONSULTING_EXTRAS_ID = 49

    START_DATE = lib.QUARTERS[quarter]['start_date']
    END_DATE = lib.QUARTERS[quarter]['end_date']

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
