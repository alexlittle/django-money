import datetime

from django.views.generic import TemplateView

from money.models import Transaction


class MonthlyTransactionsView(TemplateView):
    template_name = "money/reports/monthly_transactions.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        year = kwargs.get("year", 0)
        month = kwargs.get("month", 0)

        if year == 0:
            year = datetime.datetime.today().year
            month = datetime.datetime.today().month

        transactions = Transaction.objects.filter(date__year=year, date__month=month).order_by(
            "date"
        )

        context["transactions"] = transactions
        return context
