
import dateutil.relativedelta

from django.conf import settings

from django.shortcuts import render
from django.utils import timezone

from money.models import Transaction


def by_month_view(request):

    now = timezone.now()

    report = []

    for i in range(96, -1, -1):
        report_month = now - dateutil.relativedelta.relativedelta(months=i)

        report_row = {
            'month': report_month.month,
            'year': report_month.year,
            'sum_in': 0,
            'sum_out': 0
        }

        for k, v in settings.CURRENCIES_AVAILABLE:
            transactions = Transaction.objects \
                .filter(account__currency=k,
                        date__year=report_month.year,
                        date__month=report_month.month,
                        on_statement=True) \
                .exclude(payment_type='Transfer') \
                .exclude(account__id__in=settings.EXCLUDE_ACCOUNT_IDS)

            for t in transactions:
                report_row['sum_in'] += t.get_credit_in_base_currency()
                report_row['sum_out'] += t.get_debit_in_base_currency()

        report_row['balance'] = report_row['sum_in'] - report_row['sum_out']

        report.append(report_row)
    report.reverse()
    return render(request, 'money/reports/by_month.html',
                  {'report': report})
