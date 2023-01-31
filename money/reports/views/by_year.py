import datetime
import dateutil.relativedelta

from django.conf import settings
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from money.models import Transaction, ExchangeRate


def by_year_view(request):

    tz = timezone.get_default_timezone()
    now = datetime.datetime.now()

    report = []

    for i in range(10, -1, -1):
        report_year = now - dateutil.relativedelta.relativedelta(years=i)

        report_row = {}
        report_row['year'] = report_year.year
        report_row['sum_in'] = 0
        report_row['sum_out'] = 0
        for k, v in settings.CURRENCIES_AVAILABLE:
            transactions = Transaction.objects \
                .filter(account__currency=k,
                        date__year=report_year.year,
                        on_statement=True) \
                .exclude(payment_type='Transfer') \
                .exclude(account__id=49) \
                .extra(select={'year': "EXTRACT(year FROM date)"}) \
                .values('year') \
                .annotate(sum_in=Sum('credit'), sum_out=Sum('debit'))
            date = datetime.datetime(report_year.year, 12, 31, tzinfo=tz)

            rate = ExchangeRate.at_date(date, settings.BASE_CURRENCY, k)
            for t in transactions:
                report_row['sum_in'] += t['sum_in']/rate
                report_row['sum_out'] += t['sum_out']/rate
        report_row['balance'] = report_row['sum_in'] - report_row['sum_out']

        report.append(report_row)

    report.reverse()
    return render(request, 'money/reports/by_year.html',
                  {'report': report})
