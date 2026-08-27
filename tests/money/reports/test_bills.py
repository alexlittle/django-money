from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from money.models import Account, Transaction


class BillsViewTestBase(TestCase):
    @staticmethod
    def make_account(pk=None, currency="GBP", name="Test account"):
        kwargs = {"name": name, "currency": currency}
        if pk is not None:
            kwargs["pk"] = pk
        return Account.objects.create(**kwargs)

    @staticmethod
    def make_transaction(account, description, date, debit=0):
        return Transaction.objects.create(
            account=account,
            payment_type="Card",
            description=description,
            debit=Decimal(str(debit)),
            date=date,
        )


class BillsViewTests(BillsViewTestBase):
    def test_returns_200_and_uses_bills_template(self):
        response = self.client.get(reverse("money:bills"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "money/reports/bills.html")

    def test_electric_bills_grouped_by_year_with_totals_and_averages(self):
        account = self.make_account()
        tz = timezone.get_default_timezone()
        self.make_transaction(
            account, "Fortum - electric", timezone.datetime(2024, 1, 5, tzinfo=tz), debit=100
        )
        self.make_transaction(
            account, "Fortum - electric", timezone.datetime(2024, 2, 5, tzinfo=tz), debit=50
        )
        self.make_transaction(
            account, "Not electric", timezone.datetime(2024, 2, 5, tzinfo=tz), debit=999
        )

        response = self.client.get(reverse("money:bills"))

        rows = {row["year"]: row for row in response.context["electric"]}
        self.assertEqual(rows[2024]["total"], Decimal("150"))
        self.assertEqual(rows[2024]["no_payments"], 2)
        self.assertEqual(rows[2024]["payment_avg"], Decimal("75"))
        self.assertEqual(rows[2024]["monthly_avg"], Decimal("150") / 12)

    def test_excludes_years_before_2016(self):
        account = self.make_account()
        tz = timezone.get_default_timezone()
        self.make_transaction(
            account, "Fortum - electric", timezone.datetime(2015, 1, 5, tzinfo=tz), debit=100
        )

        response = self.client.get(reverse("money:bills"))

        years = [row["year"] for row in response.context["electric"]]
        self.assertNotIn(2015, years)

    def test_rubbish_matches_case_insensitive_substring(self):
        account = self.make_account()
        tz = timezone.get_default_timezone()
        self.make_transaction(
            account, "RUBBISH COLLECTION", timezone.datetime(2024, 1, 5, tzinfo=tz), debit=20
        )

        response = self.client.get(reverse("money:bills"))

        years = [row["year"] for row in response.context["rubbish"]]
        self.assertIn(2024, years)

    def test_phone_only_matches_elisa_on_account_39(self):
        account_39 = self.make_account(pk=39, name="Phone account")
        other_account = self.make_account(pk=40, name="Other account")
        tz = timezone.get_default_timezone()
        self.make_transaction(
            account_39, "Elisa monthly", timezone.datetime(2024, 1, 5, tzinfo=tz), debit=30
        )
        self.make_transaction(
            other_account, "Elisa monthly", timezone.datetime(2024, 1, 5, tzinfo=tz), debit=30
        )

        response = self.client.get(reverse("money:bills"))

        rows = {row["year"]: row for row in response.context["phone"]}
        self.assertEqual(rows[2024]["no_payments"], 1)

    def test_car_matches_description_starting_with_car_space(self):
        account = self.make_account()
        tz = timezone.get_default_timezone()
        self.make_transaction(
            account, "Car insurance", timezone.datetime(2024, 1, 5, tzinfo=tz), debit=40
        )
        self.make_transaction(
            account, "Carwash", timezone.datetime(2024, 1, 6, tzinfo=tz), debit=15
        )

        response = self.client.get(reverse("money:bills"))

        rows = {row["year"]: row for row in response.context["car"]}
        self.assertEqual(rows[2024]["no_payments"], 1)
