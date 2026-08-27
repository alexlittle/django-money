from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from money.models import Account, Tag, Transaction, TransactionTag


class ConsultingAnnualTestBase(TestCase):
    @staticmethod
    def make_account(pk, currency="GBP", name="Consulting"):
        return Account.objects.create(pk=pk, name=name, currency=currency)

    @staticmethod
    def make_transaction(
        account, date, credit=0, debit=0, description="Consulting income", payment_type="Card"
    ):
        return Transaction.objects.create(
            account=account,
            payment_type=payment_type,
            description=description,
            credit=Decimal(str(credit)),
            debit=Decimal(str(debit)),
            date=date,
        )


class ConsultingAnnualTests(ConsultingAnnualTestBase):
    def test_returns_200_and_uses_consulting_annual_template(self):
        response = self.client.get(reverse("money:consulting_annual", args=[2024]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "money/reports/consulting_annual.html")

    def test_includes_account_47_and_49_transactions_for_the_year(self):
        account_47 = self.make_account(pk=47)
        account_49 = self.make_account(pk=49, name="Consulting extras")
        other_account = self.make_account(pk=50, name="Other")
        tz = timezone.get_default_timezone()
        t47 = self.make_transaction(
            account_47, timezone.datetime(2024, 2, 1, tzinfo=tz), credit=500
        )
        t49 = self.make_transaction(
            account_49, timezone.datetime(2024, 3, 1, tzinfo=tz), credit=100
        )
        self.make_transaction(other_account, timezone.datetime(2024, 2, 1, tzinfo=tz), credit=999)
        self.make_transaction(account_47, timezone.datetime(2023, 2, 1, tzinfo=tz), credit=999)

        response = self.client.get(reverse("money:consulting_annual", args=[2024]))

        self.assertEqual(set(response.context["transactions"]), {t47, t49})

    def test_excludes_transfer_payment_type(self):
        account = self.make_account(pk=47)
        tz = timezone.get_default_timezone()
        self.make_transaction(
            account, timezone.datetime(2024, 2, 1, tzinfo=tz), credit=500, payment_type="Transfer"
        )

        response = self.client.get(reverse("money:consulting_annual", args=[2024]))

        self.assertEqual(list(response.context["transactions"]), [])

    def test_excludes_transactions_tagged_kollektiivi(self):
        account = self.make_account(pk=47)
        tz = timezone.get_default_timezone()
        transaction = self.make_transaction(
            account, timezone.datetime(2024, 2, 1, tzinfo=tz), credit=500
        )
        tag = Tag.objects.create(name="kollektiivi", category="kollektiivi")
        TransactionTag.objects.create(transaction=transaction, tag=tag)

        response = self.client.get(reverse("money:consulting_annual", args=[2024]))

        self.assertEqual(list(response.context["transactions"]), [])

    def test_tax_and_varma_totals_split_out_and_excluded_from_overall_totals(self):
        account = self.make_account(pk=47)
        tz = timezone.get_default_timezone()
        self.make_transaction(
            account,
            timezone.datetime(2024, 2, 1, tzinfo=tz),
            debit=100,
            description="Tax payment",
        )
        self.make_transaction(
            account,
            timezone.datetime(2024, 3, 1, tzinfo=tz),
            debit=50,
            description="Varma pension",
        )
        self.make_transaction(
            account,
            timezone.datetime(2024, 4, 1, tzinfo=tz),
            credit=1000,
            description="Consulting fee",
        )

        response = self.client.get(reverse("money:consulting_annual", args=[2024]))

        self.assertEqual(response.context["tax"]["total_debit"], Decimal("100"))
        self.assertEqual(response.context["varma"]["total_debit"], Decimal("50"))
        self.assertEqual(response.context["totals"]["total_credit"], Decimal("1000"))
        self.assertEqual(response.context["totals"]["total_debit"], Decimal("0"))
