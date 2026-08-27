from decimal import Decimal

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from money.models import Account, Valuation


class SummaryGraphTestBase(TestCase):
    @staticmethod
    def make_account(pk=None, currency="GBP", type="cash", name="Test account"):
        kwargs = {"name": name, "currency": currency, "type": type}
        if pk is not None:
            kwargs["pk"] = pk
        return Account.objects.create(**kwargs)

    @staticmethod
    def make_valuation(account, value, date=None):
        from django.utils import timezone

        return Valuation.objects.create(
            account=account, value=Decimal(str(value)), date=date or timezone.now()
        )


class SummaryGraphTests(SummaryGraphTestBase):
    def test_returns_200_and_uses_graph_template(self):
        response = self.client.get(reverse("money:graph"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "money/reports/graph.html")

    def test_balances_has_one_entry_per_month_for_last_97_months(self):
        response = self.client.get(reverse("money:graph"))
        self.assertEqual(len(response.context["balances"]), 97)

    def test_latest_balance_totals_cash_invest_and_property(self):
        cash = self.make_account(type="cash", name="Current")
        invest = self.make_account(type="invest", name="ISA")
        prop = self.make_account(type="property", name="House")
        self.make_valuation(invest, 500)
        self.make_valuation(prop, 1000)
        from money.models import Transaction

        Transaction.objects.create(
            account=cash, payment_type="Paid in", description="Salary", credit=Decimal("200")
        )

        response = self.client.get(reverse("money:graph"))

        latest = response.context["balances"][-1]
        self.assertEqual(latest["cash"], Decimal("200"))
        self.assertEqual(latest["invest"], Decimal("500"))
        self.assertEqual(latest["property"], Decimal("1000"))
        self.assertEqual(latest["total"], Decimal("1700"))

    def test_consulting_extras_account_excluded_from_cash_total(self):
        # The view excludes settings.CONSULTING_EXTRAS_ACCOUNT_ID from the
        # cash total regardless of any settings.EXCLUDE_ACCOUNT_IDS config.
        consulting_extras = self.make_account(
            pk=settings.CONSULTING_EXTRAS_ACCOUNT_ID, type="cash", name="Consulting extras"
        )
        from money.models import Transaction

        Transaction.objects.create(
            account=consulting_extras,
            payment_type="Paid in",
            description="Extras",
            credit=Decimal("999"),
        )

        response = self.client.get(reverse("money:graph"))

        latest = response.context["balances"][-1]
        self.assertEqual(latest["cash"], 0)
