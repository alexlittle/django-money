import datetime
import dateutil.relativedelta

from django.conf import settings
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from money.models import Transaction, ExchangeRate


def by_month_view(request):

    tz = timezone.get_default_timezone()
    now = datetime.datetime.now()

    report = []

    for i in range(96, -1, -1):
        report_month = now - dateutil.relativedelta.relativedelta(months=i)

        report_row = {}
        report_row['month'] = report_month.month
        report_row['year'] = report_month.year
        report_row['sum_in'] = 0
        report_row['sum_out'] = 0

        for k, v in settings.CURRENCIES_AVAILABLE:
            transactions = Transaction.objects \
                .filter(account__currency=k,
                        date__year=report_month.year,
                        date__month=report_month.month,
                        on_statement=True) \
                .exclude(payment_type='Transfer') \
                .exclude(account__id__in=settings.EXCLUDE_ACCOUNT_IDS) \
                .extra(select={'year': "EXTRACT(year FROM date)",
                               'month': "EXTRACT(month FROM date)"}) \
                .values('year', 'month') \
                .annotate(sum_in=Sum('credit'), sum_out=Sum('debit'))
            date = datetime.datetime(
                report_month.year, report_month.month, 1, tzinfo=tz)

            rate = ExchangeRate.at_date(date, settings.BASE_CURRENCY, k)
            for t in transactions:
                report_row['sum_in'] += t['sum_in']/rate
                report_row['sum_out'] += t['sum_out']/rate
        report_row['balance'] = report_row['sum_in'] - report_row['sum_out']

        report.append(report_row)
    report.reverse()
    return render(request, 'money/reports/by_month.html',
                  {'report': report})
