import datetime
import dateutil.relativedelta

from django.conf import settings
from django.shortcuts import render

from money.models import Transaction


def by_year_view(request):

    now = datetime.datetime.now()

    report = []

    for i in range(10, -1, -1):
        report_year = now - dateutil.relativedelta.relativedelta(years=i)

        report_row = {
            'year': report_year.year,
            'sum_in': 0,
            'sum_out': 0
        }

        for k, v in settings.CURRENCIES_AVAILABLE:
            transactions = Transaction.objects \
                .filter(account__currency=k,
                        date__year=report_year.year,
                        on_statement=True) \
                .exclude(payment_type='Transfer') \
                .exclude(account__id__in=settings.EXCLUDE_ACCOUNT_IDS)
            for t in transactions:
                report_row['sum_in'] += t.get_credit_in_base_currency()
                report_row['sum_out'] += t.get_debit_in_base_currency()

        report_row['balance'] = report_row['sum_in'] - report_row['sum_out']

        report.append(report_row)

    report.reverse()
    return render(request, 'money/reports/by_year.html',
                  {'report': report})
