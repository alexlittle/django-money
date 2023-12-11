import datetime

from django.views.generic import ListView
from django.db.models import Q, Sum, F
from money.models import Transaction


class MonthlyInvoicesView(ListView):
    template_name = 'money/reports/monthly_invoices.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["totals"] = self.object_list.aggregate(total_sales_tax=Sum(F("sales_tax_charged")),
                                                       total_incl_sales_tax=Sum(F("credit")))
        total_excl_sales_tax = 0
        for t in self.object_list:
            total_excl_sales_tax = total_excl_sales_tax + t.get_excl_sales_tax()

        context["total_excl_sales_tax"] = total_excl_sales_tax
        context["cross_check"] = context["totals"]["total_incl_sales_tax"] \
            - (context["totals"]["total_sales_tax"] + total_excl_sales_tax)
        year = self.kwargs["year"]
        month = self.kwargs["month"]
        context["month"] = datetime.datetime(year, month, 1)
        return context

    def get_queryset(self, **kwargs):
        year = self.kwargs["year"]
        month = self.kwargs["month"]

        result_list = Transaction.objects.filter(date__month=month, date__year=year, credit__gt=0, on_statement=True) \
            .filter(Q(account__id=47) | Q(sales_tax_charged__gt=0)) \
            .exclude(Q(file='') | Q(file=None)).order_by("date")

        return result_list
