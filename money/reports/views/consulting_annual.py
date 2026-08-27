from django.db.models import Sum
from django.views.generic import TemplateView

from money.models import Transaction


class ConsultingAnnualView(TemplateView):
    template_name = "money/reports/consulting_annual.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        CONSULTING_ID = 47
        CONSULTING_EXTRAS_ID = 49
        year = kwargs["year"]

        transactions = (
            Transaction.objects.filter(
                account_id__in=(CONSULTING_ID, CONSULTING_EXTRAS_ID), date__year=year
            )
            .exclude(payment_type="Transfer")
            .exclude(transactiontag__tag__name="kollektiivi")
        )
        # all transactions
        # excluding kollektiivi
        tax = transactions.filter(description__startswith="Tax").aggregate(
            total_credit=Sum("credit"), total_debit=Sum("debit")
        )
        varma = transactions.filter(description__startswith="Varma").aggregate(
            total_credit=Sum("credit"), total_debit=Sum("debit")
        )

        # totals
        totals = (
            transactions.exclude(description__startswith="Tax")
            .exclude(description__startswith="Varma")
            .aggregate(total_credit=Sum("credit"), total_debit=Sum("debit"))
        )

        transactions = transactions.order_by("date")

        context["year"] = year
        context["transactions"] = transactions
        context["totals"] = totals
        context["tax"] = tax
        context["varma"] = varma
        return context
