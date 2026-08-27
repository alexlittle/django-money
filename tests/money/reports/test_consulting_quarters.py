from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from money.models import Account, AccountingPeriod, Transaction


class ConsultingQuartersTestBase(TestCase):
    @staticmethod
    def make_account(pk, currency="GBP", name="Consulting"):
        return Account.objects.create(pk=pk, name=name, currency=currency)

    @staticmethod
    def make_period(start_date, end_date, title="Q1"):
        return AccountingPeriod.objects.create(
            start_date=start_date, end_date=end_date, title=title
        )

    @staticmethod
    def make_transaction(account, date, credit=0, debit=0, sales_tax_paid=0):
        return Transaction.objects.create(
            account=account,
            payment_type="Card",
            description="Consulting income",
            credit=Decimal(str(credit)),
            debit=Decimal(str(debit)),
            sales_tax_paid=Decimal(str(sales_tax_paid)),
            date=date,
        )


class ConsultingQuartersTests(ConsultingQuartersTestBase):
    def test_unknown_period_returns_404(self):
        response = self.client.get(reverse("money:consulting", args=[999999]))
        self.assertEqual(response.status_code, 404)

    def test_returns_200_and_uses_consulting_quarter_template(self):
        self.make_account(pk=47)
        tz = timezone.get_default_timezone()
        period = self.make_period(
            timezone.datetime(2024, 1, 1, tzinfo=tz), timezone.datetime(2024, 3, 31, tzinfo=tz)
        )

        response = self.client.get(reverse("money:consulting", args=[period.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "money/reports/consulting_quarter.html")

    def test_only_includes_account_47_transactions_within_the_period(self):
        consulting_account = self.make_account(pk=47)
        other_account = self.make_account(pk=48, name="Other")
        tz = timezone.get_default_timezone()
        period = self.make_period(
            timezone.datetime(2024, 1, 1, tzinfo=tz), timezone.datetime(2024, 3, 31, tzinfo=tz)
        )
        in_range = self.make_transaction(
            consulting_account, timezone.datetime(2024, 2, 1, tzinfo=tz), credit=500
        )
        self.make_transaction(
            consulting_account, timezone.datetime(2024, 4, 1, tzinfo=tz), credit=500
        )
        self.make_transaction(other_account, timezone.datetime(2024, 2, 1, tzinfo=tz), credit=500)

        response = self.client.get(reverse("money:consulting", args=[period.id]))

        transactions = [row["transaction"] for row in response.context["data"]]
        self.assertEqual(transactions, [in_range])

    def test_ex_sales_tax_only_set_for_debits_with_sales_tax_paid(self):
        consulting_account = self.make_account(pk=47)
        tz = timezone.get_default_timezone()
        period = self.make_period(
            timezone.datetime(2024, 1, 1, tzinfo=tz), timezone.datetime(2024, 3, 31, tzinfo=tz)
        )
        self.make_transaction(
            consulting_account,
            timezone.datetime(2024, 2, 1, tzinfo=tz),
            debit=120,
            sales_tax_paid=20,
        )
        self.make_transaction(
            consulting_account, timezone.datetime(2024, 2, 2, tzinfo=tz), credit=500
        )

        response = self.client.get(reverse("money:consulting", args=[period.id]))

        rows_with_ex_sales_tax = [row for row in response.context["data"] if "ex_sales_tax" in row]
        self.assertEqual(len(rows_with_ex_sales_tax), 1)
        self.assertEqual(rows_with_ex_sales_tax[0]["ex_sales_tax"], Decimal("100"))

    def test_consulting_extras_account_49_listed_separately(self):
        self.make_account(pk=47)
        extras_account = self.make_account(pk=49, name="Consulting extras")
        tz = timezone.get_default_timezone()
        period = self.make_period(
            timezone.datetime(2024, 1, 1, tzinfo=tz), timezone.datetime(2024, 3, 31, tzinfo=tz)
        )
        extras = self.make_transaction(
            extras_account, timezone.datetime(2024, 2, 1, tzinfo=tz), credit=50
        )

        response = self.client.get(reverse("money:consulting", args=[period.id]))

        self.assertEqual(list(response.context["consulting_extras"]), [extras])
