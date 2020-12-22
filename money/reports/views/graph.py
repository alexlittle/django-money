import datetime
import dateutil.relativedelta

from django.shortcuts import render
from django.utils import timezone

from money.models import Account


def graph_view(request):

    now = datetime.datetime.now()
    tz = timezone.get_default_timezone()

    balances = []

    for i in range(96, -1, -1):
        balance = {}
        old_date = now - dateutil.relativedelta.relativedelta(months=i)
        last_day = datetime.datetime(int(old_date.strftime("%Y")),
                                     int(old_date.strftime("%m")),
                                     1, 23, 59, tzinfo=tz) \
            + dateutil.relativedelta.relativedelta(day=1, months=+1, days=-1)

        cash_total = 0
        accs = Account.objects.filter(type='cash')
        for acc in accs:
            acc_balance = Account.get_balance_base_currency_at_date(
                acc, last_day)
            if acc_balance:
                cash_total += acc_balance

        invest_total = 0
        accs = Account.objects.filter(type='invest')
        for acc in accs:
            acc_balance = Account.get_valuation_base_currency_at_date(
                acc, last_day)
            if acc_balance:
                invest_total += acc_balance

        property_total = 0
        accs = Account.objects.filter(type='property')
        for acc in accs:
            acc_balance = Account.get_valuation_base_currency_at_date(
                acc, last_day)
            if acc_balance:
                property_total += acc_balance

        balance['date'] = last_day
        balance['total'] = cash_total + invest_total + property_total
        balance['cash'] = cash_total
        balance['invest'] = invest_total
        balance['property'] = property_total

        balances.append(balance)

    return render(request, 'money/reports/graph.html',
                  {'balances': balances})
