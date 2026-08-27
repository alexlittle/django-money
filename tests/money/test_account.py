from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import FieldError
from django.test import TestCase
from django.utils import timezone

from money.models import Account, ExchangeRate, Transaction, Valuation


class AccountTestBase(TestCase):
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
    def make_valuation(account, value, date=None, value_per_month=0):
        return Valuation.objects.create(
            account=account,
            value=Decimal(str(value)),
            value_per_month=Decimal(str(value_per_month)),
            date=date or timezone.now(),
        )

    @staticmethod
    def make_rate(from_cur, to_cur, rate, date=None):
        return ExchangeRate.objects.create(
            from_cur=from_cur,
            to_cur=to_cur,
            rate=Decimal(str(rate)),
            date=date or timezone.now(),
        )


class OnStatementTests(AccountTestBase):
    def test_returns_none_when_no_transactions_on_statement(self):
        account = self.make_account()
        self.assertIsNone(account.on_statement())

    def test_ignores_transactions_not_on_statement(self):
        account = self.make_account()
        self.make_transaction(account, credit=100, on_statement=False)
        self.assertIsNone(account.on_statement())

    def test_returns_credit_total_when_only_credits_on_statement(self):
        account = self.make_account()
        self.make_transaction(account, credit=100, on_statement=True)
        self.make_transaction(account, credit=50, on_statement=True)
        self.assertEqual(account.on_statement(), Decimal("150"))

    def test_returns_credit_minus_debit_when_both_on_statement(self):
        account = self.make_account()
        self.make_transaction(account, credit=100, on_statement=True)
        self.make_transaction(account, debit=30, on_statement=True)
        self.assertEqual(account.on_statement(), Decimal("70"))

    def test_returns_negative_total_when_only_debits_on_statement(self):
        # Every Transaction row has both a credit and a debit column
        # (defaulting to 0), so a debit-only row still makes Sum("credit")
        # resolve to 0 rather than None - the None case only occurs when
        # zero rows match at all (see test_returns_none_when_no_transactions...).
        account = self.make_account()
        self.make_transaction(account, debit=30, on_statement=True)
        self.assertEqual(account.on_statement(), Decimal("-30"))

    def test_only_includes_this_accounts_transactions(self):
        account = self.make_account(name="A")
        other = self.make_account(name="B")
        self.make_transaction(account, credit=100, on_statement=True)
        self.make_transaction(other, credit=999, on_statement=True)
        self.assertEqual(account.on_statement(), Decimal("100"))


class GetBalanceTests(AccountTestBase):
    def test_returns_zero_when_no_transactions(self):
        account = self.make_account()
        self.assertEqual(account.get_balance(), 0)

    def test_sums_credit_minus_debit(self):
        account = self.make_account()
        self.make_transaction(account, credit=100)
        self.make_transaction(account, debit=40)
        self.assertEqual(account.get_balance(), Decimal("60"))

    def test_only_includes_this_accounts_transactions(self):
        account = self.make_account(name="A")
        other = self.make_account(name="B")
        self.make_transaction(account, credit=100)
        self.make_transaction(other, credit=999)
        self.assertEqual(account.get_balance(), Decimal("100"))


class GetBalanceAtDateTests(AccountTestBase):
    def test_returns_zero_when_no_transactions(self):
        account = self.make_account()
        self.assertEqual(Account.get_balance_at_date(account, timezone.now()), 0)

    def test_includes_transactions_on_or_before_date(self):
        account = self.make_account()
        now = timezone.now()
        self.make_transaction(account, credit=100, date=now - timedelta(days=1))
        self.make_transaction(account, credit=50, date=now)

        self.assertEqual(Account.get_balance_at_date(account, now), Decimal("150"))

    def test_excludes_transactions_after_date(self):
        account = self.make_account()
        now = timezone.now()
        self.make_transaction(account, credit=100, date=now - timedelta(days=1))
        self.make_transaction(account, credit=50, date=now + timedelta(days=1))

        self.assertEqual(Account.get_balance_at_date(account, now), Decimal("100"))

    def test_tag_filter_raises_field_error(self):
        # Known bug: this branch filters/annotates on
        # `transactiontag__percent`, a field that no longer exists on
        # TransactionTag (removed in migration 0013). Any caller passing
        # `tag=` currently gets a FieldError. No production code path
        # passes `tag=` today, so this is latent rather than live.
        account = self.make_account()
        with self.assertRaises(FieldError):
            Account.get_balance_at_date(account, timezone.now(), tag="rent")


class GetValuationTests(AccountTestBase):
    def test_get_valuation_returns_none_when_no_valuations(self):
        account = self.make_account()
        self.assertIsNone(account.get_valuation())

    def test_get_valuation_returns_the_latest_positive_valuation(self):
        account = self.make_account()
        now = timezone.now()
        self.make_valuation(account, 100, date=now - timedelta(days=30))
        latest = self.make_valuation(account, 150, date=now)

        self.assertEqual(account.get_valuation(), latest)

    def test_get_valuation_ignores_non_positive_values(self):
        account = self.make_account()
        self.make_valuation(account, 0, date=timezone.now())
        self.assertIsNone(account.get_valuation())

    def test_get_monthly_valuation_returns_none_when_no_valuations(self):
        account = self.make_account()
        self.assertIsNone(account.get_monthly_valuation())

    def test_get_monthly_valuation_returns_latest_with_positive_value_per_month(self):
        account = self.make_account()
        now = timezone.now()
        self.make_valuation(account, 100, value_per_month=0, date=now - timedelta(days=30))
        latest = self.make_valuation(account, 100, value_per_month=5, date=now)

        self.assertEqual(account.get_monthly_valuation(), latest)

    def test_get_valuation_at_date_returns_none_when_none_recorded_before_date(self):
        account = self.make_account()
        self.make_valuation(account, 100, date=timezone.now() + timedelta(days=1))
        self.assertIsNone(Account.get_valuation_at_date(account, timezone.now()))

    def test_get_valuation_at_date_returns_latest_at_or_before_date(self):
        account = self.make_account()
        now = timezone.now()
        older = self.make_valuation(account, 100, date=now - timedelta(days=30))
        self.make_valuation(account, 200, date=now + timedelta(days=1))

        self.assertEqual(Account.get_valuation_at_date(account, now), older)

    def test_get_valuation_at_date_includes_non_positive_values(self):
        # Unlike get_valuation(), this lookup has no value__gt=0 filter.
        account = self.make_account()
        zero_valuation = self.make_valuation(account, 0, date=timezone.now())
        self.assertEqual(Account.get_valuation_at_date(account, timezone.now()), zero_valuation)


class BaseCurrencyConversionTests(AccountTestBase):
    def test_get_balance_base_currency_returns_balance_directly_for_base_currency_account(self):
        account = self.make_account(currency="GBP")
        self.make_transaction(account, credit=100)
        self.assertEqual(account.get_balance_base_currency(), Decimal("100"))

    def test_get_balance_base_currency_converts_using_most_recent_rate(self):
        account = self.make_account(currency="EUR")
        self.make_transaction(account, credit=115)
        self.make_rate("GBP", "EUR", "1.15")

        self.assertEqual(account.get_balance_base_currency(), Decimal("100"))

    def test_get_balance_base_currency_at_date_uses_rate_at_date(self):
        # The same `date` argument bounds both the balance cutoff and the
        # exchange rate lookup, so querying between the two rates should
        # use the earlier one even though a later rate exists.
        account = self.make_account(currency="EUR")
        now = timezone.now()
        query_date = now - timedelta(days=7)
        self.make_transaction(account, credit=115, date=now - timedelta(days=10))
        self.make_rate("GBP", "EUR", "1.10", date=now - timedelta(days=20))
        self.make_rate("GBP", "EUR", "1.15", date=now - timedelta(days=5))

        result = Account.get_balance_base_currency_at_date(account, query_date)
        self.assertAlmostEqual(result, Decimal("115") / Decimal("1.10"))

    def test_get_balance_base_currency_at_date_returns_zero_when_no_balance(self):
        account = self.make_account(currency="EUR")
        self.make_rate("GBP", "EUR", "1.15")
        self.assertEqual(Account.get_balance_base_currency_at_date(account, timezone.now()), 0)

    def test_get_balance_base_currency_at_date_returns_balance_directly_for_base_currency(self):
        account = self.make_account(currency="GBP")
        now = timezone.now()
        self.make_transaction(account, credit=100, date=now - timedelta(days=1))

        self.assertEqual(Account.get_balance_base_currency_at_date(account, now), Decimal("100"))

    def test_get_valuation_base_currency_returns_zero_when_no_valuation(self):
        account = self.make_account(currency="EUR")
        self.assertEqual(account.get_valuation_base_currency(), 0)

    def test_get_valuation_base_currency_returns_zero_for_base_currency_when_no_valuation(self):
        account = self.make_account(currency="GBP")
        self.assertEqual(account.get_valuation_base_currency(), 0)

    def test_get_valuation_base_currency_returns_value_directly_for_base_currency(self):
        account = self.make_account(currency="GBP")
        self.make_valuation(account, 200)
        self.assertEqual(account.get_valuation_base_currency(), Decimal("200"))

    def test_get_valuation_base_currency_converts_for_non_base_currency(self):
        account = self.make_account(currency="EUR")
        self.make_valuation(account, 115)
        self.make_rate("GBP", "EUR", "1.15")

        self.assertEqual(account.get_valuation_base_currency(), Decimal("100"))

    def test_get_monthly_valuation_base_currency_returns_zero_when_none(self):
        account = self.make_account(currency="EUR")
        self.assertEqual(account.get_monthly_valuation_base_currency(), 0)

    def test_get_monthly_valuation_base_currency_returns_zero_for_base_currency_when_none(self):
        account = self.make_account(currency="GBP")
        self.assertEqual(account.get_monthly_valuation_base_currency(), 0)

    def test_get_monthly_valuation_base_currency_converts_for_non_base_currency(self):
        account = self.make_account(currency="EUR")
        self.make_valuation(account, 100, value_per_month=11.5)
        self.make_rate("GBP", "EUR", "1.15")

        self.assertEqual(account.get_monthly_valuation_base_currency(), Decimal("10"))

    def test_get_valuation_base_currency_at_date_returns_zero_when_none(self):
        account = self.make_account(currency="GBP")
        self.assertEqual(Account.get_valuation_base_currency_at_date(account, timezone.now()), 0)

    def test_get_valuation_base_currency_at_date_returns_zero_for_non_base_when_none(self):
        account = self.make_account(currency="EUR")
        self.make_rate("GBP", "EUR", "1.15")
        self.assertEqual(Account.get_valuation_base_currency_at_date(account, timezone.now()), 0)

    def test_get_valuation_base_currency_at_date_returns_value_directly_for_base_currency(self):
        account = self.make_account(currency="GBP")
        now = timezone.now()
        self.make_valuation(account, 200, date=now - timedelta(days=1))

        self.assertEqual(Account.get_valuation_base_currency_at_date(account, now), Decimal("200"))

    def test_get_valuation_base_currency_at_date_converts_for_non_base_currency(self):
        account = self.make_account(currency="EUR")
        now = timezone.now()
        self.make_valuation(account, 115, date=now - timedelta(days=10))
        self.make_rate("GBP", "EUR", "1.15", date=now - timedelta(days=5))

        self.assertEqual(Account.get_valuation_base_currency_at_date(account, now), Decimal("100"))

    def test_get_paid_in_base_currency_at_date_returns_zero_when_no_credits(self):
        account = self.make_account(currency="GBP")
        self.assertEqual(Account.get_paid_in_base_currency_at_date(account, timezone.now()), 0)

    def test_get_paid_in_base_currency_at_date_returns_zero_for_non_base_when_no_credits(self):
        account = self.make_account(currency="EUR")
        self.make_rate("GBP", "EUR", "1.15")
        self.assertEqual(Account.get_paid_in_base_currency_at_date(account, timezone.now()), 0)

    def test_get_paid_in_base_currency_at_date_sums_credits_for_base_currency(self):
        account = self.make_account(currency="GBP")
        now = timezone.now()
        self.make_transaction(account, credit=100, date=now - timedelta(days=1))
        self.make_transaction(account, credit=50, date=now)
        self.make_transaction(account, credit=999, date=now + timedelta(days=1))

        self.assertEqual(Account.get_paid_in_base_currency_at_date(account, now), Decimal("150"))

    def test_get_paid_in_base_currency_at_date_converts_for_non_base_currency(self):
        account = self.make_account(currency="EUR")
        now = timezone.now()
        self.make_transaction(account, credit=115, date=now - timedelta(days=10))
        self.make_rate("GBP", "EUR", "1.15", date=now - timedelta(days=5))

        self.assertEqual(Account.get_paid_in_base_currency_at_date(account, now), Decimal("100"))


class CompoundInterestTests(AccountTestBase):
    def test_returns_zero_when_no_valuation_at_start_of_period(self):
        account = self.make_account()
        self.make_valuation(account, 150, date=timezone.now())
        self.assertEqual(account.get_compound_interest(years=5), 0)

    def test_returns_zero_when_no_valuation_at_end_of_period(self):
        account = self.make_account()
        self.assertEqual(account.get_compound_interest(years=5), 0)

    def test_calculates_annualised_growth_rate(self):
        account = self.make_account()
        now = timezone.now()
        self.make_valuation(account, 100, date=now - timedelta(days=730))
        self.make_valuation(account, 121, date=now)

        rate = account.get_compound_interest(years=2)
        self.assertAlmostEqual(rate, 10.0, places=6)

    def test_raises_zero_division_error_when_start_valuation_is_zero(self):
        # Known bug: get_compound_interest() only checks the start/end
        # Valuation rows for truthiness, not their `value`. A `value=0`
        # row (e.g. an investment account before its first deposit) is
        # truthy, so this reaches float(end) / float(0) and blows up.
        account = self.make_account()
        now = timezone.now()
        self.make_valuation(account, 0, date=now - timedelta(days=730))
        self.make_valuation(account, 100, date=now)

        with self.assertRaises(ZeroDivisionError):
            account.get_compound_interest(years=2)


class AggregateTotalsTests(AccountTestBase):
    def test_get_balance_total_sums_active_accounts_of_matching_type_and_currency(self):
        a = self.make_account(currency="GBP", type="cash", name="A")
        b = self.make_account(currency="GBP", type="cash", name="B")
        other_currency = self.make_account(currency="EUR", type="cash", name="C")
        other_type = self.make_account(currency="GBP", type="invest", name="D")
        inactive = self.make_account(currency="GBP", type="cash", active=False, name="E")

        self.make_transaction(a, credit=100)
        self.make_transaction(b, credit=50)
        self.make_transaction(other_currency, credit=999)
        self.make_transaction(other_type, credit=999)
        self.make_transaction(inactive, credit=999)

        self.assertEqual(Account.get_balance_total("cash", "GBP"), Decimal("150"))

    def test_get_on_statment_total_sums_statement_balances(self):
        a = self.make_account(currency="GBP", type="cash", name="A")
        b = self.make_account(currency="GBP", type="cash", name="B")
        self.make_transaction(a, credit=100, on_statement=True)
        self.make_transaction(a, credit=999, on_statement=False)
        self.make_transaction(b, credit=50, on_statement=True)

        self.assertEqual(Account.get_on_statment_total("cash", "GBP"), Decimal("150"))

    def test_get_balance_base_currency_total_converts_non_base_accounts(self):
        gbp_account = self.make_account(currency="GBP", type="cash", name="A")
        eur_account = self.make_account(currency="EUR", type="cash", name="B")
        self.make_transaction(gbp_account, credit=100)
        self.make_transaction(eur_account, credit=115)
        self.make_rate("GBP", "EUR", "1.15")

        # Note: currency= filters which accounts are included, but the
        # totals across calls for GBP and EUR are meant to be combined
        # by the caller; each call itself totals one currency group.
        self.assertEqual(Account.get_balance_base_currency_total("cash", "EUR"), Decimal("100"))

    def test_get_valuation_total_skips_accounts_with_no_valuation(self):
        self.make_account(currency="GBP", type="invest", name="A")
        with_valuation = self.make_account(currency="GBP", type="invest", name="B")
        self.make_valuation(with_valuation, 100)

        self.assertEqual(Account.get_valuation_total("invest", "GBP"), Decimal("100"))

    def test_get_valuation_total_sums_valuations_when_all_accounts_have_one(self):
        a = self.make_account(currency="GBP", type="invest", name="A")
        b = self.make_account(currency="GBP", type="invest", name="B")
        self.make_valuation(a, 100)
        self.make_valuation(b, 50)

        self.assertEqual(Account.get_valuation_total("invest", "GBP"), Decimal("150"))

    def test_get_valuation_base_currency_total_converts_non_base_accounts(self):
        account = self.make_account(currency="EUR", type="invest", name="A")
        self.make_valuation(account, 115)
        self.make_rate("GBP", "EUR", "1.15")

        self.assertEqual(Account.get_valuation_base_currency_total("invest", "EUR"), Decimal("100"))

    def test_get_val_base_currency_total_ignores_currency_and_sums_across_all(self):
        gbp_account = self.make_account(currency="GBP", type="property", name="A")
        eur_account = self.make_account(currency="EUR", type="property", name="B")
        self.make_valuation(gbp_account, 100)
        self.make_valuation(eur_account, 115)
        self.make_rate("GBP", "EUR", "1.15")

        self.assertEqual(Account.get_val_base_currency_total("property"), Decimal("200"))

    def test_get_monthly_val_base_currency_total_sums_across_all_currencies(self):
        gbp_account = self.make_account(currency="GBP", type="pension", name="A")
        eur_account = self.make_account(currency="EUR", type="pension", name="B")
        self.make_valuation(gbp_account, 100, value_per_month=10)
        self.make_valuation(eur_account, 100, value_per_month=11.5)
        self.make_rate("GBP", "EUR", "1.15")

        self.assertEqual(Account.get_monthly_val_base_currency_total("pension"), Decimal("20"))
