from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from money.models import Account, AccountingPeriod, Tag, Transaction, TransactionTag


class TagsByCategoryViewTestBase(TestCase):
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
    def make_transaction_tag(transaction, tag):
        return TransactionTag.objects.create(transaction=transaction, tag=tag)

    @staticmethod
    def make_period(start_date, end_date, title="Q1", active=True):
        return AccountingPeriod.objects.create(
            start_date=start_date, end_date=end_date, title=title, active=active
        )


class TagsByCategoryViewTests(TagsByCategoryViewTestBase):
    def test_returns_200_and_uses_tags_by_category_template(self):
        response = self.client.get(reverse("money:tags_by_category", args=["house"]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "money/reports/tags_by_category.html")

    def test_context_has_the_requested_category(self):
        response = self.client.get(reverse("money:tags_by_category", args=["house"]))
        self.assertEqual(response.context["category"], "house")

    def test_totals_by_year_sums_only_transactions_tagged_in_this_category(self):
        account = self.make_account()
        tag = self.make_tag(category="house")
        other_tag = self.make_tag(name="Petrol", category="car")
        tz = timezone.get_default_timezone()
        t1 = self.make_transaction(account, timezone.datetime(2024, 1, 1, tzinfo=tz), credit=100)
        t2 = self.make_transaction(account, timezone.datetime(2024, 6, 1, tzinfo=tz), debit=40)
        self.make_transaction_tag(t1, tag)
        self.make_transaction_tag(t2, tag)
        t3 = self.make_transaction(account, timezone.datetime(2024, 6, 1, tzinfo=tz), credit=999)
        self.make_transaction_tag(t3, other_tag)

        response = self.client.get(reverse("money:tags_by_category", args=["house"]))

        totals = {row["year"]: row for row in response.context["totals_by_year"]}
        self.assertEqual(totals[2024]["sum_in"], Decimal("100"))
        self.assertEqual(totals[2024]["sum_out"], Decimal("40"))
        self.assertEqual(totals[2024]["balance"], Decimal("60"))

    def test_periods_summarised_only_for_active_periods_that_have_started(self):
        account = self.make_account()
        tag = self.make_tag(category="house")
        now = timezone.now()
        active_period = self.make_period(now - timezone.timedelta(days=30), now, title="Current")
        future_period = self.make_period(
            now + timezone.timedelta(days=30), now + timezone.timedelta(days=60), title="Future"
        )
        transaction = self.make_transaction(account, now - timezone.timedelta(days=10), credit=50)
        self.make_transaction_tag(transaction, tag)

        response = self.client.get(reverse("money:tags_by_category", args=["house"]))

        periods = {p["id"]: p for p in response.context["periods"]}
        self.assertIn(active_period.id, periods)
        self.assertNotIn(future_period.id, periods)
        self.assertEqual(periods[active_period.id]["sum_in"], Decimal("50"))

    def test_without_period_id_lists_all_matching_transactions(self):
        account = self.make_account()
        tag = self.make_tag(category="house")
        tz = timezone.get_default_timezone()
        older = self.make_transaction(account, timezone.datetime(2024, 1, 1, tzinfo=tz))
        newer = self.make_transaction(account, timezone.datetime(2024, 6, 1, tzinfo=tz))
        self.make_transaction_tag(older, tag)
        self.make_transaction_tag(newer, tag)

        response = self.client.get(reverse("money:tags_by_category", args=["house"]))

        self.assertEqual(list(response.context["transactions"]), [newer, older])
        self.assertNotIn("period", response.context)

    def test_with_period_id_restricts_to_that_periods_date_range(self):
        account = self.make_account()
        tag = self.make_tag(category="house")
        tz = timezone.get_default_timezone()
        period = self.make_period(
            timezone.datetime(2024, 1, 1, tzinfo=tz), timezone.datetime(2024, 3, 31, tzinfo=tz)
        )
        in_range = self.make_transaction(account, timezone.datetime(2024, 2, 1, tzinfo=tz))
        out_of_range = self.make_transaction(account, timezone.datetime(2024, 6, 1, tzinfo=tz))
        self.make_transaction_tag(in_range, tag)
        self.make_transaction_tag(out_of_range, tag)

        response = self.client.get(reverse("money:tags_by_category", args=["house", period.id]))

        self.assertEqual(list(response.context["transactions"]), [in_range])
        self.assertEqual(response.context["period"], period)

    def test_unknown_period_returns_404(self):
        response = self.client.get(reverse("money:tags_by_category", args=["house", 999999]))
        self.assertEqual(response.status_code, 404)
