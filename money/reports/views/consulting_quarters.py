from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from money.models import Account, AccountingPeriod, Transaction


class ConsultingQuartersView(TemplateView):
    template_name = "money/reports/consulting_quarter.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        CONSULTING_ID = 47
        CONSULTING_EXTRAS_ID = 49

        ap = get_object_or_404(AccountingPeriod, pk=kwargs["period_id"])
        START_DATE = ap.start_date
        END_DATE = ap.end_date

        consulting_account = Account.objects.get(pk=CONSULTING_ID)
        consulting = Transaction.objects.filter(
            account_id=CONSULTING_ID, date__gte=START_DATE, date__lte=END_DATE
        ).order_by("date")

        data = []
        for c in consulting:
            obj = {
                "transaction": c,
                "balance": Account.get_balance_base_currency_at_date(c.account, c.date),
            }
            if c.debit != 0 and c.sales_tax_paid != 0:
                obj["ex_sales_tax"] = c.debit - c.sales_tax_paid
            data.append(obj)

        opening_balance = Account.get_balance_base_currency_at_date(consulting_account, START_DATE)
        closing_balance = Account.get_balance_base_currency_at_date(consulting_account, END_DATE)

        consulting_extras = Transaction.objects.filter(
            account_id=CONSULTING_EXTRAS_ID, date__gte=START_DATE, date__lte=END_DATE
        ).order_by("date")

        context["data"] = data
        context["opening_balance"] = opening_balance
        context["closing_balance"] = closing_balance
        context["start_date"] = START_DATE
        context["end_date"] = END_DATE
        context["consulting_extras"] = consulting_extras
        return context
