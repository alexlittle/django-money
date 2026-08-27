from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from money.models import Account, RegularPayment, Transaction, Valuation


class HomeViewTestBase(TestCase):
    @staticmethod
    def make_account(currency="GBP", type="cash", active=True, name="Test account"):
        return Account.objects.create(name=name, currency=currency, type=type, active=active)

    @staticmethod
    def make_transaction(account, credit=0, debit=0, on_statement=False, date=None):
        return Transaction.objects.create(
            account=account,
            payment_type="Card",
            description="Test transaction",
            credit=Decimal(str(credit)),
            debit=Decimal(str(debit)),
            on_statement=on_statement,
            date=date or timezone.now(),
        )

    @staticmethod
    def make_valuation(account, value, date=None):
        return Valuation.objects.create(
            account=account, value=Decimal(str(value)), date=date or timezone.now()
        )


class HomeViewTests(HomeViewTestBase):
    def test_returns_200_and_uses_home_template(self):
        response = self.client.get(reverse("money:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "money/home.html")

    def test_cash_accounts_grouped_by_currency_with_correct_totals(self):
        gbp_account = self.make_account(currency="GBP", type="cash", name="Current")
        self.make_transaction(gbp_account, credit=100, on_statement=True)
        self.make_transaction(gbp_account, debit=30, on_statement=True)

        response = self.client.get(reverse("money:home"))

        by_currency = {c["currency"]: c for c in response.context["cash_accounts"]}
        self.assertEqual(by_currency["GBP"]["total_balance"], Decimal("70"))
        self.assertEqual(by_currency["GBP"]["total_on_statement"], Decimal("70"))
        self.assertIn(gbp_account, by_currency["GBP"]["account"])
        self.assertEqual(by_currency["EUR"]["total_balance"], 0)

    def test_inactive_cash_accounts_are_excluded(self):
        self.make_account(currency="GBP", type="cash", active=False, name="Closed")

        response = self.client.get(reverse("money:home"))

        by_currency = {c["currency"]: c for c in response.context["cash_accounts"]}
        self.assertEqual(list(by_currency["GBP"]["account"]), [])

    def test_invest_accounts_with_no_valuation_do_not_crash(self):
        # Regression test for the get_valuation_total AttributeError bug:
        # an invest account with no Valuation row must not blow up the
        # homepage.
        self.make_account(currency="GBP", type="invest", name="ISA")

        response = self.client.get(reverse("money:home"))

        self.assertEqual(response.status_code, 200)
        by_currency = {c["currency"]: c for c in response.context["invest_accounts"]}
        self.assertEqual(by_currency["GBP"]["total_valuation"], 0)

    def test_invest_accounts_total_valuation_sums_across_accounts(self):
        a = self.make_account(currency="GBP", type="invest", name="A")
        b = self.make_account(currency="GBP", type="invest", name="B")
        self.make_valuation(a, 100)
        self.make_valuation(b, 50)

        response = self.client.get(reverse("money:home"))

        by_currency = {c["currency"]: c for c in response.context["invest_accounts"]}
        self.assertEqual(by_currency["GBP"]["total_valuation"], Decimal("150"))

    def test_property_accounts_included_regardless_of_currency(self):
        gbp_property = self.make_account(currency="GBP", type="property", name="House")
        eur_property = self.make_account(currency="EUR", type="property", name="Mokki")

        response = self.client.get(reverse("money:home"))

        accounts = list(response.context["property"]["accounts"])
        self.assertIn(gbp_property, accounts)
        self.assertIn(eur_property, accounts)

    def test_pension_accounts_included_with_totals(self):
        pension = self.make_account(currency="GBP", type="pension", name="Workplace pension")
        self.make_valuation(pension, 1000)

        response = self.client.get(reverse("money:home"))

        self.assertIn(pension, list(response.context["pensions"]["accounts"]))
        self.assertEqual(response.context["pensions"]["total_base_currency"], Decimal("1000"))


class UpdateRegularPaymentsOnHomeViewTests(HomeViewTestBase):
    def test_due_regular_payment_creates_a_transaction_and_advances_next_date(self):
        account = self.make_account(currency="GBP", type="cash")
        now = timezone.now()
        payment = RegularPayment.objects.create(
            account=account,
            description="Rent",
            credit=0,
            debit=500,
            payment_type="Transfer",
            next_date=now - timedelta(days=1),
            end_date=now + timedelta(days=365),
        )

        self.client.get(reverse("money:home"))

        self.assertEqual(Transaction.objects.filter(account=account, description="Rent").count(), 1)
        transaction = Transaction.objects.get(account=account, description="Rent")
        self.assertEqual(transaction.debit, Decimal("500"))

        payment.refresh_from_db()
        self.assertEqual(payment.next_date, now - timedelta(days=1) + timedelta(days=31))

    def test_future_regular_payment_is_not_processed(self):
        account = self.make_account(currency="GBP", type="cash")
        now = timezone.now()
        RegularPayment.objects.create(
            account=account,
            description="Future payment",
            credit=0,
            debit=500,
            payment_type="Transfer",
            next_date=now + timedelta(days=10),
            end_date=now + timedelta(days=365),
        )

        self.client.get(reverse("money:home"))

        self.assertFalse(Transaction.objects.filter(account=account).exists())
