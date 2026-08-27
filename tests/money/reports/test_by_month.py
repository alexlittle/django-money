from decimal import Decimal

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from money.models import Account, Transaction


class ByMonthViewTestBase(TestCase):
    @staticmethod
    def make_account(pk=None, currency="GBP", name="Test account"):
        kwargs = {"name": name, "currency": currency}
        if pk is not None:
            kwargs["pk"] = pk
        return Account.objects.create(**kwargs)

    @staticmethod
    def make_transaction(account, date, credit=0, debit=0, on_statement=True, payment_type="Card"):
        return Transaction.objects.create(
            account=account,
            payment_type=payment_type,
            description="Test transaction",
            credit=Decimal(str(credit)),
            debit=Decimal(str(debit)),
            on_statement=on_statement,
            date=date,
        )


class ByMonthViewTests(ByMonthViewTestBase):
    def test_returns_200_and_uses_by_month_template(self):
        response = self.client.get(reverse("money:by_month"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "money/reports/by_month.html")

    def test_report_has_one_row_per_month_for_last_97_months_newest_first(self):
        # The view builds the list oldest-first then reverses it, so the
        # current month ends up at index 0 and the oldest at index -1.
        response = self.client.get(reverse("money:by_month"))
        report = response.context["report"]
        self.assertEqual(len(report), 97)
        now = timezone.now()
        self.assertEqual(report[0]["year"], now.year)
        self.assertEqual(report[0]["month"], now.month)

    def test_sums_in_and_out_for_current_month_on_statement_transactions(self):
        account = self.make_account()
        now = timezone.now()
        self.make_transaction(account, now, credit=100, on_statement=True)
        self.make_transaction(account, now, debit=30, on_statement=True)

        response = self.client.get(reverse("money:by_month"))

        current = response.context["report"][0]
        self.assertEqual(current["sum_in"], Decimal("100"))
        self.assertEqual(current["sum_out"], Decimal("30"))
        self.assertEqual(current["balance"], Decimal("70"))

    def test_ignores_transactions_not_on_statement(self):
        account = self.make_account()
        now = timezone.now()
        self.make_transaction(account, now, credit=100, on_statement=False)

        response = self.client.get(reverse("money:by_month"))

        current = response.context["report"][0]
        self.assertEqual(current["sum_in"], 0)

    def test_ignores_transfer_payments(self):
        account = self.make_account()
        now = timezone.now()
        self.make_transaction(account, now, credit=100, on_statement=True, payment_type="Transfer")

        response = self.client.get(reverse("money:by_month"))

        current = response.context["report"][0]
        self.assertEqual(current["sum_in"], 0)

    def test_excludes_accounts_in_settings_exclude_account_ids(self):
        excluded_id = settings.EXCLUDE_ACCOUNT_IDS[0]
        account = self.make_account(pk=excluded_id)
        now = timezone.now()
        self.make_transaction(account, now, credit=100, on_statement=True)

        response = self.client.get(reverse("money:by_month"))

        current = response.context["report"][0]
        self.assertEqual(current["sum_in"], 0)
