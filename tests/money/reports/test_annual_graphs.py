from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from money.models import Account, Transaction


class AnnualGraphsViewTestBase(TestCase):
    @staticmethod
    def make_account(currency="GBP", name="Test account"):
        return Account.objects.create(name=name, currency=currency)

    @staticmethod
    def make_transaction(account, date, credit=0):
        return Transaction.objects.create(
            account=account,
            payment_type="Card",
            description="Test transaction",
            credit=Decimal(str(credit)),
            date=date,
        )


class AnnualGraphsViewTests(AnnualGraphsViewTestBase):
    def test_returns_200_and_uses_annual_graphs_template(self):
        response = self.client.get(reverse("money:graphs_annual", args=[2024]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "money/reports/annual_graphs.html")

    def test_context_has_requested_year(self):
        response = self.client.get(reverse("money:graphs_annual", args=[2024]))
        self.assertEqual(response.context["year"], 2024)

    def test_only_includes_transactions_from_the_requested_year(self):
        account = self.make_account()
        tz = timezone.get_default_timezone()
        in_year = self.make_transaction(
            account, timezone.datetime(2024, 6, 1, tzinfo=tz), credit=10
        )
        self.make_transaction(account, timezone.datetime(2023, 6, 1, tzinfo=tz), credit=20)

        response = self.client.get(reverse("money:graphs_annual", args=[2024]))

        self.assertEqual(list(response.context["transactions"]), [in_year])
