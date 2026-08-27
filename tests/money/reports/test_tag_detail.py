from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from money.models import Account, AccountingPeriod, Tag, Transaction, TransactionTag


class TagDetailViewTestBase(TestCase):
    @staticmethod
    def make_account(currency="GBP", name="Test account"):
        return Account.objects.create(name=name, currency=currency)

    @staticmethod
    def make_tag(name="Groceries", category="house"):
        return Tag.objects.create(name=name, category=category)

    @staticmethod
    def make_transaction(account, date, credit=0, debit=0):
        return Transaction.objects.create(
            account=account,
            payment_type="Card",
            description="Test transaction",
            credit=Decimal(str(credit)),
            debit=Decimal(str(debit)),
            date=date,
        )

    @staticmethod
    def make_transaction_tag(transaction, tag, allocation_credit=0, allocation_debit=0):
        return TransactionTag.objects.create(
            transaction=transaction,
            tag=tag,
            allocation_credit=Decimal(str(allocation_credit)),
            allocation_debit=Decimal(str(allocation_debit)),
        )

    @staticmethod
    def make_period(start_date, end_date, title="Q1"):
        return AccountingPeriod.objects.create(
            start_date=start_date, end_date=end_date, title=title
        )


class TagDetailViewTests(TagDetailViewTestBase):
    def test_unknown_tag_returns_404(self):
        response = self.client.get(reverse("money:tag_detail", args=[999999]))
        self.assertEqual(response.status_code, 404)

    def test_returns_200_and_uses_tag_detail_template(self):
        tag = self.make_tag()
        response = self.client.get(reverse("money:tag_detail", args=[tag.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "money/reports/tag_detail.html")

    def test_totals_by_year_sums_credit_and_debit_for_this_tag_only(self):
        account = self.make_account()
        tag = self.make_tag()
        other_tag = self.make_tag(name="Other")
        tz = timezone.get_default_timezone()
        t1 = self.make_transaction(account, timezone.datetime(2024, 1, 1, tzinfo=tz))
        t2 = self.make_transaction(account, timezone.datetime(2024, 6, 1, tzinfo=tz))
        self.make_transaction_tag(t1, tag, allocation_credit=100)
        self.make_transaction_tag(t2, tag, allocation_debit=40)
        self.make_transaction_tag(t2, other_tag, allocation_debit=999)

        response = self.client.get(reverse("money:tag_detail", args=[tag.id]))

        totals = {row["year"]: row for row in response.context["totals_by_year"]}
        self.assertEqual(totals[2024]["sum_in"], Decimal("100"))
        self.assertEqual(totals[2024]["sum_out"], Decimal("40"))

    def test_without_period_lists_all_transaction_tags_newest_first(self):
        account = self.make_account()
        tag = self.make_tag()
        tz = timezone.get_default_timezone()
        t_old = self.make_transaction(account, timezone.datetime(2024, 1, 1, tzinfo=tz))
        t_new = self.make_transaction(account, timezone.datetime(2024, 6, 1, tzinfo=tz))
        tt_old = self.make_transaction_tag(t_old, tag, allocation_credit=10)
        tt_new = self.make_transaction_tag(t_new, tag, allocation_credit=20)

        response = self.client.get(reverse("money:tag_detail", args=[tag.id]))

        self.assertEqual(list(response.context["transactiontags"]), [tt_new, tt_old])
        self.assertNotIn("period", response.context)

    def test_with_period_restricts_to_that_periods_date_range(self):
        account = self.make_account()
        tag = self.make_tag()
        tz = timezone.get_default_timezone()
        period = self.make_period(
            timezone.datetime(2024, 1, 1, tzinfo=tz), timezone.datetime(2024, 3, 31, tzinfo=tz)
        )
        t_in = self.make_transaction(account, timezone.datetime(2024, 2, 1, tzinfo=tz))
        t_out = self.make_transaction(account, timezone.datetime(2024, 6, 1, tzinfo=tz))
        tt_in = self.make_transaction_tag(t_in, tag, allocation_credit=10)
        self.make_transaction_tag(t_out, tag, allocation_credit=20)

        response = self.client.get(reverse("money:tag_detail", args=[tag.id, period.id]))

        self.assertEqual(list(response.context["transactiontags"]), [tt_in])
        self.assertEqual(response.context["period"], period)

    def test_unknown_period_returns_404(self):
        tag = self.make_tag()
        response = self.client.get(reverse("money:tag_detail", args=[tag.id, 999999]))
        self.assertEqual(response.status_code, 404)
