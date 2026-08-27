from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from money.models import Account, Transaction


class MonthlyInvoicesViewTestBase(TestCase):
    @staticmethod
    def make_account(pk=None, currency="GBP", name="Consulting"):
        kwargs = {"name": name, "currency": currency}
        if pk is not None:
            kwargs["pk"] = pk
        return Account.objects.create(**kwargs)

    @staticmethod
    def make_transaction(
        account,
        date,
        credit=0,
        sales_tax_charged=0,
        on_statement=True,
        has_file=True,
    ):
        return Transaction.objects.create(
            account=account,
            payment_type="Paid in",
            description="Invoice",
            credit=Decimal(str(credit)),
            sales_tax_charged=Decimal(str(sales_tax_charged)),
            on_statement=on_statement,
            date=date,
            file="transaction/invoice.pdf" if has_file else "",
        )


class MonthlyInvoicesViewTests(MonthlyInvoicesViewTestBase):
    def test_no_invoices_for_the_month_renders_zero_totals(self):
        response = self.client.get(reverse("money:monthly_invoices", args=[2024, 3]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["object_list"]), [])
        self.assertEqual(response.context["totals"]["total_sales_tax"], 0)
        self.assertEqual(response.context["totals"]["total_incl_sales_tax"], 0)
        self.assertEqual(response.context["total_excl_sales_tax"], 0)
        self.assertEqual(response.context["cross_check"], 0)

    def test_returns_200_and_uses_monthly_invoices_template(self):
        account = self.make_account(pk=47)
        tz = timezone.get_default_timezone()
        self.make_transaction(account, timezone.datetime(2024, 3, 10, tzinfo=tz), credit=120)

        response = self.client.get(reverse("money:monthly_invoices", args=[2024, 3]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "money/reports/monthly_invoices.html")

    def test_context_has_month_as_a_date(self):
        account = self.make_account(pk=47)
        tz = timezone.get_default_timezone()
        self.make_transaction(account, timezone.datetime(2024, 3, 10, tzinfo=tz), credit=120)

        response = self.client.get(reverse("money:monthly_invoices", args=[2024, 3]))

        self.assertEqual(response.context["month"], timezone.datetime(2024, 3, 1))

    def test_includes_account_47_invoice_with_file_for_the_month(self):
        account = self.make_account(pk=47)
        tz = timezone.get_default_timezone()
        invoice = self.make_transaction(
            account,
            timezone.datetime(2024, 3, 10, tzinfo=tz),
            credit=120,
            sales_tax_charged=20,
        )

        response = self.client.get(reverse("money:monthly_invoices", args=[2024, 3]))

        self.assertEqual(list(response.context["object_list"]), [invoice])

    def test_excludes_transactions_without_a_file(self):
        account = self.make_account(pk=47)
        tz = timezone.get_default_timezone()
        self.make_transaction(
            account, timezone.datetime(2024, 3, 10, tzinfo=tz), credit=120, has_file=False
        )
        control = self.make_transaction(
            account, timezone.datetime(2024, 3, 11, tzinfo=tz), credit=50, sales_tax_charged=10
        )

        response = self.client.get(reverse("money:monthly_invoices", args=[2024, 3]))

        self.assertEqual(list(response.context["object_list"]), [control])

    def test_excludes_non_account_47_transactions_with_no_sales_tax_charged(self):
        control_account = self.make_account(pk=47)
        control = self.make_transaction(
            control_account,
            timezone.datetime(2024, 3, 9, tzinfo=self.tz()),
            credit=50,
        )
        other_account = self.make_account(pk=99, name="Other")
        self.make_transaction(
            other_account,
            timezone.datetime(2024, 3, 10, tzinfo=self.tz()),
            credit=120,
            sales_tax_charged=0,
        )

        response = self.client.get(reverse("money:monthly_invoices", args=[2024, 3]))

        self.assertEqual(list(response.context["object_list"]), [control])

    def test_includes_non_account_47_transactions_with_sales_tax_charged(self):
        account = self.make_account(pk=99, name="Other")
        tz = timezone.get_default_timezone()
        invoice = self.make_transaction(
            account, timezone.datetime(2024, 3, 10, tzinfo=tz), credit=120, sales_tax_charged=20
        )

        response = self.client.get(reverse("money:monthly_invoices", args=[2024, 3]))

        self.assertEqual(list(response.context["object_list"]), [invoice])

    def test_totals_and_cross_check(self):
        account = self.make_account(pk=47)
        tz = timezone.get_default_timezone()
        self.make_transaction(
            account,
            timezone.datetime(2024, 3, 10, tzinfo=tz),
            credit=120,
            sales_tax_charged=20,
        )
        self.make_transaction(
            account,
            timezone.datetime(2024, 3, 15, tzinfo=tz),
            credit=60,
            sales_tax_charged=10,
        )

        response = self.client.get(reverse("money:monthly_invoices", args=[2024, 3]))

        self.assertEqual(response.context["totals"]["total_sales_tax"], Decimal("30"))
        self.assertEqual(response.context["totals"]["total_incl_sales_tax"], Decimal("180"))
        self.assertEqual(response.context["total_excl_sales_tax"], Decimal("150"))
        self.assertEqual(response.context["cross_check"], 0)

    @staticmethod
    def tz():
        return timezone.get_default_timezone()
