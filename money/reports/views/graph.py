import datetime

import dateutil.relativedelta
from django.conf import settings
from django.utils import timezone
from django.views.generic import TemplateView

from money.models import Account
from money.reports.balance_history import monthly_balances


def _last_day_of_month(base_date, tz):
    return datetime.datetime(
        int(base_date.strftime("%Y")), int(base_date.strftime("%m")), 1, 23, 59, tzinfo=tz
    ) + dateutil.relativedelta.relativedelta(day=1, months=+1, days=-1)


class SummaryGraph(TemplateView):
    template_name = "money/reports/graph.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        now = datetime.datetime.now()
        tz = timezone.get_default_timezone()

        accounts = Account.objects.filter(type__in=["cash", "invest", "property"])
        cash_accounts = [
            a
            for a in accounts
            if a.type == "cash" and a.pk != settings.CONSULTING_EXTRAS_ACCOUNT_ID
        ]
        invest_accounts = [a for a in accounts if a.type == "invest"]
        property_accounts = [a for a in accounts if a.type == "property"]

        month_ends = []
        for i in range(96, -1, -1):
            old_date = now - dateutil.relativedelta.relativedelta(months=i)
            last_day = _last_day_of_month(old_date, tz)
            boundary = datetime.datetime(
                old_date.year, old_date.month, 1, tzinfo=tz
            ) + dateutil.relativedelta.relativedelta(months=1)
            month_ends.append((last_day, boundary))

        context["balances"] = monthly_balances(
            month_ends, tz, cash_accounts, invest_accounts, property_accounts
        )
        return context
