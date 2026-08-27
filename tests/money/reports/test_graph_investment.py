from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from money.models import Account, Valuation


class GraphInvestmentViewTestBase(TestCase):
    @staticmethod
    def make_account(currency="GBP", type="invest", active=True, name="ISA"):
        return Account.objects.create(name=name, currency=currency, type=type, active=active)

    @staticmethod
    def make_valuation(account, value, date=None):
        return Valuation.objects.create(
            account=account, value=Decimal(str(value)), date=date or timezone.now()
        )


class GraphInvestmentViewTests(GraphInvestmentViewTestBase):
    def test_returns_200_and_uses_investment_graph_template(self):
        response = self.client.get(reverse("money:investment_graph"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "money/reports/investment-graph.html")

    def test_includes_active_investment_accounts_with_valuations_history(self):
        account = self.make_account()
        self.make_valuation(account, 500)

        response = self.client.get(reverse("money:investment_graph"))

        accounts = response.context["accounts"]
        self.assertEqual(len(accounts), 1)
        self.assertEqual(accounts[0]["account"], account)
        self.assertEqual(len(accounts[0]["valuations"]), 97)
        self.assertEqual(accounts[0]["valuations"][-1]["value"], Decimal("500"))

    def test_excludes_inactive_investment_accounts(self):
        self.make_account(active=False)

        response = self.client.get(reverse("money:investment_graph"))

        self.assertEqual(response.context["accounts"], [])

    def test_excludes_non_investment_accounts(self):
        Account.objects.create(name="Current", currency="GBP", type="cash")

        response = self.client.get(reverse("money:investment_graph"))

        self.assertEqual(response.context["accounts"], [])
