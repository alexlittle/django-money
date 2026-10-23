"""Tests for the values produced by the summary graph.

These pin the exact figures the view produces for a known data set, so the
calculation can be refactored without changing any numbers. Expected values are
worked out by hand in the comments below, not copied from the code's output.
A month includes everything dated before the start of the following month.

Months are addressed as "n months ago": n=0 is the current month and
``balances[96 - n]`` is its entry.
"""

import calendar
import datetime
import random
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from money.models import Account, ExchangeRate, Transaction, Valuation


def month_start(n):
    """First day of the month n months before the current one."""
    today = datetime.date.today()
    return datetime.date(today.year, today.month, 1) - relativedelta(months=n)


def at(n, day, hour=12, minute=0, second=0):
    """Timezone-aware datetime on a given day of the month n months ago."""
    start = month_start(n)
    return timezone.make_aware(
        datetime.datetime(start.year, start.month, day, hour, minute, second)
    )


def last_day_of(n):
    start = month_start(n)
    return calendar.monthrange(start.year, start.month)[1]


class GraphValuesBase(TestCase):
    @staticmethod
    def account(name, type="cash", currency="GBP", active=True):
        return Account.objects.create(name=name, type=type, currency=currency, active=active)

    @staticmethod
    def credit(account, amount, when):
        return Transaction.objects.create(
            account=account,
            payment_type="Paid in",
            description="credit",
            credit=Decimal(str(amount)),
            date=when,
        )

    @staticmethod
    def debit(account, amount, when):
        return Transaction.objects.create(
            account=account,
            payment_type="Card",
            description="debit",
            debit=Decimal(str(amount)),
            date=when,
        )

    @staticmethod
    def valuation(account, value, on):
        return Valuation.objects.create(account=account, value=Decimal(str(value)), date=on)

    @staticmethod
    def rate(from_cur, to_cur, rate, when):
        return ExchangeRate.objects.create(
            from_cur=from_cur, to_cur=to_cur, rate=Decimal(str(rate)), date=when
        )

    def balances(self):
        response = self.client.get(reverse("money:graph"))
        self.assertEqual(response.status_code, 200)
        return response.context["balances"]

    def months_ago(self, n):
        return self.balances()[96 - n]


class GraphKnownDataTests(GraphValuesBase):
    """One data set covering both currencies, rate changes and month-end edges."""

    def setUp(self):
        current = self.account("Current")
        euro = self.account("Euro", currency="EUR")
        isa = self.account("ISA", type="invest")
        euro_fund = self.account("Euro fund", type="invest", currency="EUR")
        house = self.account("House", type="property")

        # GBP -> EUR rate: 1.25 from 6 months ago, 2.0 from 2 months ago.
        self.rate("GBP", "EUR", "1.25", at(6, 1))
        self.rate("GBP", "EUR", "2.0", at(2, 1))

        self.credit(current, 1000, at(5, 10))
        # Late on the last day of the month: still counted in that month.
        self.credit(current, 11, at(4, last_day_of(4), 23, 59, 0))
        self.debit(current, 300, at(3, 15))
        self.credit(current, 77, at(3, last_day_of(3), 23, 59, 30))

        self.credit(euro, 200, at(4, 5))

        self.valuation(isa, 400, month_start(6) + relativedelta(days=19))
        self.valuation(isa, 450, month_start(2) + relativedelta(days=9))
        self.valuation(euro_fund, 500, month_start(4) + relativedelta(days=2))
        self.valuation(house, 100000, month_start(8) + relativedelta(days=4))
        self.valuation(house, 110000, month_start(1))

    # Cash (GBP + EUR converted at the rate in force at the month's cut-off):
    #   n>=6: 0 | n=5: 1000 | n=4: 1011 + 200/1.25 = 1171
    #   n=3: 1011 - 300 + 77 + 200/1.25 = 948 | n<=2: 788 + 200/2.0 = 888
    EXPECTED_CASH = {5: 1000, 4: 1171, 3: 948, 2: 888, 1: 888, 0: 888}

    # Investments (EUR fund also converted at the cut-off rate):
    #   ISA 400 from n=6, 450 from n=2 | Euro fund 500 from n=4: 400 at 1.25, 250 at 2.0
    EXPECTED_INVEST = {6: 400, 5: 400, 4: 800, 3: 800, 2: 700, 1: 700, 0: 700}

    # Property: 100000 from n=8, 110000 from n=1.
    EXPECTED_PROPERTY = {8: 100000, 7: 100000, 6: 100000, 5: 100000, 4: 100000, 3: 100000,
                         2: 100000, 1: 110000, 0: 110000}  # fmt: skip

    def test_every_month_matches_hand_calculated_values(self):
        balances = self.balances()
        for n in range(96, -1, -1):
            expected_cash = self.EXPECTED_CASH.get(n, 0)
            expected_invest = self.EXPECTED_INVEST.get(n, 0)
            expected_property = self.EXPECTED_PROPERTY.get(n, 0)
            with self.subTest(months_ago=n):
                b = balances[96 - n]
                self.assertEqual(b["cash"], Decimal(expected_cash))
                self.assertEqual(b["invest"], Decimal(expected_invest))
                self.assertEqual(b["property"], Decimal(expected_property))
                self.assertEqual(
                    b["total"], Decimal(expected_cash + expected_invest + expected_property)
                )

    def test_months_are_ordered_oldest_first_and_end_on_last_day(self):
        balances = self.balances()
        dates = [b["date"] for b in balances]
        self.assertEqual(dates, sorted(dates))
        for n in (96, 50, 3, 0):
            d = balances[96 - n]["date"]
            start = month_start(n)
            self.assertEqual((d.year, d.month, d.day), (start.year, start.month, last_day_of(n)))
            self.assertEqual((d.hour, d.minute), (23, 59))

    def test_page_needs_only_a_few_queries(self):
        with CaptureQueriesContext(connection) as queries:
            self.balances()
        self.assertLessEqual(len(queries), 6)


class GraphEdgeCaseTests(GraphValuesBase):
    def test_no_data_gives_zeroes_in_every_month(self):
        for b in self.balances():
            self.assertEqual((b["cash"], b["invest"], b["property"], b["total"]), (0, 0, 0, 0))

    def test_non_base_currency_without_any_rate_is_not_converted(self):
        euro = self.account("Euro", currency="EUR")
        self.credit(euro, 200, at(2, 5))
        self.assertEqual(self.months_ago(2)["cash"], Decimal(200))

    def test_inverse_rate_is_used_when_only_the_opposite_pair_exists(self):
        # Only EUR -> GBP stored (0.5), so GBP -> EUR is taken as 1 / 0.5 = 2.
        euro = self.account("Euro", currency="EUR")
        self.rate("EUR", "GBP", "0.5", at(4, 1))
        self.credit(euro, 200, at(2, 5))
        self.assertEqual(self.months_ago(2)["cash"], Decimal(100))

    def test_rate_dated_after_the_month_is_ignored(self):
        euro = self.account("Euro", currency="EUR")
        self.rate("GBP", "EUR", "4", at(1, 1))
        self.credit(euro, 200, at(3, 5))
        self.assertEqual(self.months_ago(3)["cash"], Decimal(200))  # no rate yet: 1
        self.assertEqual(self.months_ago(1)["cash"], Decimal(50))  # 200 / 4

    def test_inactive_accounts_are_still_included(self):
        closed = self.account("Closed", active=False)
        self.credit(closed, 5, at(2, 5))
        self.assertEqual(self.months_ago(2)["cash"], Decimal(5))

    def test_valuation_dated_after_the_month_is_ignored(self):
        isa = self.account("ISA", type="invest")
        self.valuation(isa, 400, month_start(2) + relativedelta(days=9))
        self.assertEqual(self.months_ago(3)["invest"], 0)
        self.assertEqual(self.months_ago(2)["invest"], Decimal(400))

    def test_latest_valuation_on_or_before_cutoff_wins(self):
        house = self.account("House", type="property")
        self.valuation(house, 100, month_start(3))
        self.valuation(house, 200, month_start(2) + relativedelta(day=last_day_of(2)))
        self.assertEqual(self.months_ago(3)["property"], Decimal(100))
        self.assertEqual(self.months_ago(2)["property"], Decimal(200))

    def test_credits_and_debits_net_off_and_can_go_negative(self):
        current = self.account("Current")
        self.credit(current, 100, at(2, 5))
        self.debit(current, 250, at(2, 6))
        self.assertEqual(self.months_ago(2)["cash"], Decimal(-150))
        self.assertEqual(self.months_ago(2)["total"], Decimal(-150))


class GraphMatchesPerAccountCalculationTests(GraphValuesBase):
    """Cross-check the page against the per-account model methods on random data."""

    def test_matches_account_methods_for_every_month(self):
        rng = random.Random(1234)
        cash = [
            self.account("Cash GBP 1"),
            self.account("Cash GBP 2", active=False),
            self.account("Cash EUR 1", currency="EUR"),
            self.account("Cash EUR 2", currency="EUR"),
        ]
        invest = [self.account("ISA", type="invest"), self.account("EUR fund", "invest", "EUR")]
        prop = [self.account("House", "property"), self.account("EUR flat", "property", "EUR")]

        # Rates in both directions, so the direct and inverse paths are both used.
        for n in (40, 30, 22, 15, 9, 3):
            self.rate("GBP", "EUR", f"{rng.uniform(1.05, 1.4):.5f}", at(n, rng.randint(1, 28)))
        for n in (60, 25, 5):
            self.rate("EUR", "GBP", f"{rng.uniform(0.7, 0.95):.5f}", at(n, rng.randint(1, 28)))

        for acc in cash:
            for _ in range(60):
                n = rng.randint(0, 80)
                # Mix of mid-month and last-day entries, including late on the last day.
                day = rng.choice([rng.randint(1, 28), last_day_of(n)])
                when = at(n, day, rng.randint(0, 23), rng.randint(0, 59), rng.randint(0, 59))
                amount = rng.randint(1, 50000) / 100
                if rng.random() < 0.6:
                    self.credit(acc, amount, when)
                else:
                    self.debit(acc, amount, when)

        for acc in invest + prop:
            for n in rng.sample(range(0, 90), 12):
                day = rng.randint(1, last_day_of(n))
                self.valuation(
                    acc, rng.randint(1000, 900000) / 100, month_start(n).replace(day=day)
                )

        # Decimal addition rounds, so add in the order the view does (model ordering).
        def in_view_order(accounts):
            return sorted(accounts, key=lambda a: (a.order, a.name))

        cash, invest, prop = in_view_order(cash), in_view_order(invest), in_view_order(prop)

        for entry in self.balances():
            last_day = entry["date"]
            next_month = datetime.datetime(last_day.year, last_day.month, 1, tzinfo=last_day.tzinfo)
            cutoff = next_month + relativedelta(months=1) - datetime.timedelta(microseconds=1)

            expected_cash = sum(
                Account.get_balance_base_currency_at_date(a, cutoff) or 0 for a in cash
            )
            expected_invest = sum(
                Account.get_valuation_base_currency_at_date(a, cutoff) for a in invest
            )
            expected_property = sum(
                Account.get_valuation_base_currency_at_date(a, cutoff) for a in prop
            )
            with self.subTest(month=last_day.strftime("%Y-%m")):
                self.assertEqual(entry["cash"], expected_cash)
                self.assertEqual(entry["invest"], expected_invest)
                self.assertEqual(entry["property"], expected_property)
