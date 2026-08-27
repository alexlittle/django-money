from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from money.models import Account, AccountingPeriod, Tag, Transaction, TransactionTag


class TagsByPeriodTestBase(TestCase):
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
    def make_period(start_date, end_date, title="Q1", active=True):
        return AccountingPeriod.objects.create(
            start_date=start_date, end_date=end_date, title=title, active=active
        )


class TagsByYearViewTests(TagsByPeriodTestBase):
    def test_returns_200_and_uses_tags_by_period_template(self):
        response = self.client.get(reverse("money:tags_all"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "money/reports/tags_by_period.html")

    def test_no_year_defaults_to_current_year(self):
        response = self.client.get(reverse("money:tags_all"))
        self.assertEqual(response.context["year"], timezone.now().year)

    def test_explicit_year_is_used(self):
        response = self.client.get(reverse("money:tags_by_year", args=[2023]))
        self.assertEqual(response.context["year"], 2023)

    def test_years_list_runs_from_2022_to_the_current_year(self):
        response = self.client.get(reverse("money:tags_all"))
        current_year = timezone.now().year
        self.assertEqual(response.context["years"], list(range(2022, current_year + 1)))

    def test_categories_and_tags_only_include_the_requested_year(self):
        account = self.make_account()
        tag = self.make_tag(name="Groceries", category="house")
        tz = timezone.get_default_timezone()
        in_year = self.make_transaction(account, timezone.datetime(2024, 1, 1, tzinfo=tz))
        out_year = self.make_transaction(account, timezone.datetime(2023, 1, 1, tzinfo=tz))
        self.make_transaction_tag(in_year, tag, allocation_credit=100)
        self.make_transaction_tag(out_year, tag, allocation_credit=999)

        response = self.client.get(reverse("money:tags_by_year", args=[2024]))

        categories = {c["category"]: c for c in response.context["categories"]}
        self.assertEqual(categories["house"]["sum_in"], Decimal("100"))

        tags = {t["tag"]: t for t in response.context["tags"]}
        self.assertEqual(tags[tag]["sum_in"], Decimal("100"))


class TagsByPeriodViewTests(TagsByPeriodTestBase):
    def test_unknown_period_returns_404(self):
        response = self.client.get(reverse("money:tags_by_period", args=[999999]))
        self.assertEqual(response.status_code, 404)

    def test_returns_200_and_uses_tags_by_period_template(self):
        period = self.make_period(timezone.now(), timezone.now())
        response = self.client.get(reverse("money:tags_by_period", args=[period.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "money/reports/tags_by_period.html")
        self.assertEqual(response.context["period"], period)

    def test_renders_and_sums_tags_and_categories_for_transactions_within_the_period(self):
        account = self.make_account()
        tag = self.make_tag(name="Groceries", category="house")
        tz = timezone.get_default_timezone()
        period = self.make_period(
            timezone.datetime(2024, 1, 1, tzinfo=tz), timezone.datetime(2024, 3, 31, tzinfo=tz)
        )
        in_range = self.make_transaction(account, timezone.datetime(2024, 2, 1, tzinfo=tz))
        out_of_range = self.make_transaction(account, timezone.datetime(2024, 6, 1, tzinfo=tz))
        self.make_transaction_tag(in_range, tag, allocation_credit=100, allocation_debit=10)
        self.make_transaction_tag(out_of_range, tag, allocation_credit=999)

        response = self.client.get(reverse("money:tags_by_period", args=[period.id]))

        self.assertEqual(response.status_code, 200)

        tags = {t["tag"]: t for t in response.context["tags"]}
        self.assertEqual(tags[tag]["sum_in"], Decimal("100"))
        self.assertEqual(tags[tag]["sum_out"], Decimal("10"))

        categories = {c["category"]: c for c in response.context["categories"]}
        self.assertEqual(categories["house"]["sum_in"], Decimal("100"))
