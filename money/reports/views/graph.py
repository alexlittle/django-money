import datetime

import dateutil.relativedelta
from django.conf import settings
from django.utils import timezone
from django.views.generic import TemplateView

from money.models import Account


def _last_day_of_month(base_date, tz):
    return datetime.datetime(
        int(base_date.strftime("%Y")), int(base_date.strftime("%m")), 1, 23, 59, tzinfo=tz
    ) + dateutil.relativedelta.relativedelta(day=1, months=+1, days=-1)


def _sum_balances_at_date(accounts, at_date, get_balance):
    total = 0
    for acc in accounts:
        acc_balance = get_balance(acc, at_date)
        if acc_balance:
            total += acc_balance
    return total


def _balance_for_month(last_day):
    cash_total = _sum_balances_at_date(
        Account.objects.filter(type="cash").exclude(pk=settings.CONSULTING_EXTRAS_ACCOUNT_ID),
        last_day,
        Account.get_balance_base_currency_at_date,
    )
    invest_total = _sum_balances_at_date(
        Account.objects.filter(type="invest"), last_day, Account.get_valuation_base_currency_at_date
    )
    property_total = _sum_balances_at_date(
        Account.objects.filter(type="property"),
        last_day,
        Account.get_valuation_base_currency_at_date,
    )

    return {
        "date": last_day,
        "total": cash_total + invest_total + property_total,
        "cash": cash_total,
        "invest": invest_total,
        "property": property_total,
    }


class SummaryGraph(TemplateView):
    template_name = "money/reports/graph.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        now = datetime.datetime.now()
        tz = timezone.get_default_timezone()

        balances = []
        for i in range(96, -1, -1):
            old_date = now - dateutil.relativedelta.relativedelta(months=i)
            last_day = _last_day_of_month(old_date, tz)
            balances.append(_balance_for_month(last_day))

        context["balances"] = balances
        return context
