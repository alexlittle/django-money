from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from money.models import Account, Transaction


class MonthlyTransactionsViewTestBase(TestCase):
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


class MonthlyTransactionsViewTests(MonthlyTransactionsViewTestBase):
    def test_returns_200_and_uses_monthly_transactions_template(self):
        response = self.client.get(reverse("money:monthly_transactions"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "money/reports/monthly_transactions.html")

    def test_defaults_to_current_month_when_no_year_or_month_given(self):
        account = self.make_account()
        now = timezone.now()
        this_month = self.make_transaction(account, now, credit=10)
        tz = timezone.get_default_timezone()
        last_year = self.make_transaction(
            account, timezone.datetime(now.year - 1, now.month, 1, 12, tzinfo=tz), credit=20
        )

        response = self.client.get(reverse("money:monthly_transactions"))

        self.assertIn(this_month, response.context["transactions"])
        self.assertNotIn(last_year, response.context["transactions"])

    def test_filters_by_explicit_year_and_month_ordered_by_date(self):
        account = self.make_account()
        tz = timezone.get_default_timezone()
        older = self.make_transaction(
            account, timezone.datetime(2024, 3, 5, 12, tzinfo=tz), credit=10
        )
        newer = self.make_transaction(
            account, timezone.datetime(2024, 3, 20, 12, tzinfo=tz), credit=20
        )
        self.make_transaction(account, timezone.datetime(2024, 4, 5, 12, tzinfo=tz), credit=30)

        response = self.client.get(reverse("money:monthly_transactions", args=[2024, 3]))

        self.assertEqual(list(response.context["transactions"]), [older, newer])
