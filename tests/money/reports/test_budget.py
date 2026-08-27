from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from money.models import Account, AccountingPeriod, Tag, Transaction, TransactionTag


class BudgetTestBase(TestCase):
    @staticmethod
    def make_account(pk=None, currency="GBP", name="Test account"):
        kwargs = {"name": name, "currency": currency}
        if pk is not None:
            kwargs["pk"] = pk
        return Account.objects.create(**kwargs)

    @staticmethod
    def make_tag(name="Groceries", category="house", active=True):
        return Tag.objects.create(name=name, category=category, active=active)

    @staticmethod
    def make_transaction(account, date, credit=0, debit=0, payment_type="Card"):
        return Transaction.objects.create(
            account=account,
            payment_type=payment_type,
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


class BudgetViewTests(BudgetTestBase):
    def test_returns_200_and_uses_budget_template(self):
        response = self.client.get(reverse("money:budget_all"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "money/reports/budget.html")

    def test_lists_only_active_periods(self):
        tz = timezone.get_default_timezone()
        active = self.make_period(
            timezone.datetime(2024, 1, 1, tzinfo=tz),
            timezone.datetime(2024, 3, 31, tzinfo=tz),
            active=True,
        )
        inactive = self.make_period(
            timezone.datetime(2023, 1, 1, tzinfo=tz),
            timezone.datetime(2023, 3, 31, tzinfo=tz),
            active=False,
        )

        response = self.client.get(reverse("money:budget_all"))

        object_list = list(response.context["object_list"])
        self.assertIn(active, object_list)
        self.assertNotIn(inactive, object_list)


class BudgetByPeriodViewTests(BudgetTestBase):
    def test_unknown_period_returns_404(self):
        response = self.client.get(reverse("money:budget_by_period", args=[999999]))
        self.assertEqual(response.status_code, 404)

    def test_returns_200_and_uses_budget_by_period_template(self):
        tz = timezone.get_default_timezone()
        period = self.make_period(
            timezone.datetime(2024, 1, 1, tzinfo=tz), timezone.datetime(2024, 3, 31, tzinfo=tz)
        )
        response = self.client.get(reverse("money:budget_by_period", args=[period.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "money/reports/budget_by_period.html")
        self.assertEqual(response.context["period"], period)

    def test_income_grouped_by_category_excludes_transfers_and_kollektiivi(self):
        account = self.make_account()
        tz = timezone.get_default_timezone()
        period = self.make_period(
            timezone.datetime(2024, 1, 1, tzinfo=tz), timezone.datetime(2024, 3, 31, tzinfo=tz)
        )
        income_tag = self.make_tag(name="Salary", category="business")
        kollektiivi_tag = self.make_tag(name="kollektiivi", category="kollektiivi")

        salary_transaction = self.make_transaction(
            account, timezone.datetime(2024, 2, 1, tzinfo=tz), credit=1000
        )
        self.make_transaction_tag(salary_transaction, income_tag, allocation_credit=1000)

        transfer_transaction = self.make_transaction(
            account, timezone.datetime(2024, 2, 2, tzinfo=tz), credit=500, payment_type="Transfer"
        )
        self.make_transaction_tag(transfer_transaction, income_tag, allocation_credit=500)

        kollektiivi_transaction = self.make_transaction(
            account, timezone.datetime(2024, 2, 3, tzinfo=tz), credit=200
        )
        self.make_transaction_tag(kollektiivi_transaction, kollektiivi_tag, allocation_credit=200)

        response = self.client.get(reverse("money:budget_by_period", args=[period.id]))

        self.assertEqual(response.context["income"]["business"], Decimal("1000"))
        self.assertEqual(response.context["income_total"], Decimal("1000"))

    def test_personal_expenses_grouped_by_house_and_personal_tags(self):
        account = self.make_account()
        tz = timezone.get_default_timezone()
        period = self.make_period(
            timezone.datetime(2024, 1, 1, tzinfo=tz), timezone.datetime(2024, 3, 31, tzinfo=tz)
        )
        groceries_tag = self.make_tag(name="Groceries", category="house")

        groceries_transaction = self.make_transaction(
            account, timezone.datetime(2024, 2, 1, tzinfo=tz), debit=150
        )
        self.make_transaction_tag(groceries_transaction, groceries_tag, allocation_debit=150)

        response = self.client.get(reverse("money:budget_by_period", args=[period.id]))

        personal_expenses = {e["name"]: e for e in response.context["personal_expenses"]}
        self.assertEqual(personal_expenses["Groceries"]["total"], Decimal("150"))
        self.assertEqual(response.context["personal_expenses_total"], Decimal("150"))

    def test_business_expenses_grouped_by_business_design_rental_tags(self):
        account = self.make_account()
        tz = timezone.get_default_timezone()
        period = self.make_period(
            timezone.datetime(2024, 1, 1, tzinfo=tz), timezone.datetime(2024, 3, 31, tzinfo=tz)
        )
        hosting_tag = self.make_tag(name="Hosting", category="business")

        hosting_transaction = self.make_transaction(
            account, timezone.datetime(2024, 2, 1, tzinfo=tz), debit=75
        )
        self.make_transaction_tag(hosting_transaction, hosting_tag, allocation_debit=75)

        response = self.client.get(reverse("money:budget_by_period", args=[period.id]))

        business_expenses = {e["name"]: e for e in response.context["business_expenses"]}
        self.assertEqual(business_expenses["Hosting"]["total"], Decimal("75"))
        self.assertEqual(response.context["business_expenses_total"], Decimal("75"))

    def test_untagged_transaction_within_period_is_missing(self):
        account = self.make_account()
        tz = timezone.get_default_timezone()
        period = self.make_period(
            timezone.datetime(2024, 1, 1, tzinfo=tz), timezone.datetime(2024, 3, 31, tzinfo=tz)
        )
        untagged = self.make_transaction(
            account, timezone.datetime(2024, 2, 1, tzinfo=tz), debit=42
        )

        response = self.client.get(reverse("money:budget_by_period", args=[period.id]))

        self.assertIn(untagged, list(response.context["missing_transactions"]))

    def test_account_49_excluded_from_missing_transactions(self):
        account = self.make_account(pk=49, name="Consulting extras")
        tz = timezone.get_default_timezone()
        period = self.make_period(
            timezone.datetime(2024, 1, 1, tzinfo=tz), timezone.datetime(2024, 3, 31, tzinfo=tz)
        )
        self.make_transaction(account, timezone.datetime(2024, 2, 1, tzinfo=tz), debit=42)

        response = self.client.get(reverse("money:budget_by_period", args=[period.id]))

        self.assertEqual(list(response.context["missing_transactions"]), [])

    def test_tagged_transaction_is_not_also_counted_as_missing(self):
        account = self.make_account()
        tz = timezone.get_default_timezone()
        period = self.make_period(
            timezone.datetime(2024, 1, 1, tzinfo=tz), timezone.datetime(2024, 3, 31, tzinfo=tz)
        )
        tag = self.make_tag(name="Groceries", category="house")
        tagged = self.make_transaction(account, timezone.datetime(2024, 2, 1, tzinfo=tz), debit=50)
        self.make_transaction_tag(tagged, tag, allocation_debit=50)

        response = self.client.get(reverse("money:budget_by_period", args=[period.id]))

        self.assertNotIn(tagged, list(response.context["missing_transactions"]))
