import datetime
import dateutil.relativedelta

from django.shortcuts import render
from django.utils import timezone

from money.models import Account


def graph_investment_view(request):

    accounts = []

    now = datetime.datetime.now()
    tz = timezone.get_default_timezone()

    accs = Account.objects.filter(type='invest', active=True)

    for account in accs:
        resp_account = {}
        resp_account['account'] = account
        valuations = []

        for i in range(96, -1, -1):
            valuation = {}
            old_date = now - dateutil.relativedelta.relativedelta(months=i)
            last_day = datetime.datetime(int(old_date.strftime("%Y")),
                                         int(old_date.strftime("%m")),
                                         1, 23, 59, tzinfo=tz) \
                + dateutil.relativedelta.relativedelta(day=1, months=+1, days=-1)

            acc_value = Account.get_valuation_base_currency_at_date(account, last_day)
            acc_paid_in = Account.get_paid_in_base_currency_at_date(account, last_day)

            valuation['date'] = last_day
            valuation['value'] = acc_value
            valuation['paid_in'] = acc_paid_in
            valuations.append(valuation)

        resp_account['valuations'] = valuations

        resp_account['rate_10_year'] =  account.get_compound_interest(10)
        resp_account['rate_7_year'] = account.get_compound_interest(7)
        resp_account['rate_5_year'] = account.get_compound_interest(5)
        resp_account['rate_3_year'] = account.get_compound_interest(3)
        resp_account['rate_2_year'] = account.get_compound_interest(2)
        resp_account['rate_1_year'] = account.get_compound_interest(1)
        accounts.append(resp_account)

    return render(request, 'money/reports/investment-graph.html', {'accounts': accounts})
