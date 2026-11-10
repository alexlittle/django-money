import datetime

import dateutil.relativedelta
from django.utils import timezone
from django.views.generic import TemplateView

from money.models import Account
from money.reports.charts import valuation_chart


class GraphInvestmentView(TemplateView):
    template_name = "money/reports/investment-graph.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        accounts = []

        now = datetime.datetime.now()
        tz = timezone.get_default_timezone()

        accs = Account.objects.filter(type="invest", active=True)

        for account in accs:
            resp_account = {}
            resp_account["account"] = account
            valuations = []

            for i in range(96, -1, -1):
                valuation = {}
                old_date = now - dateutil.relativedelta.relativedelta(months=i)
                last_day = datetime.datetime(
                    int(old_date.strftime("%Y")), int(old_date.strftime("%m")), 1, 23, 59, tzinfo=tz
                ) + dateutil.relativedelta.relativedelta(day=1, months=+1, days=-1)

                acc_value = Account.get_valuation_base_currency_at_date(account, last_day)
                acc_paid_in = Account.get_paid_in_base_currency_at_date(account, last_day)

                valuation["date"] = last_day
                valuation["value"] = acc_value
                valuation["paid_in"] = acc_paid_in
                valuations.append(valuation)

            resp_account["valuations"] = valuations
            resp_account["chart"] = valuation_chart(valuations)
            resp_account["chart_id"] = f"chart-{account.pk}"

            resp_account["returns"] = [
                {"years": years, "rate": account.get_annualised_return(years)}
                for years in (1, 2, 3, 5, 7, 10)
            ]
            accounts.append(resp_account)

        context["accounts"] = accounts
        return context
