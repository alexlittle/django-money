from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from money.models import ExchangeRate


class ExchangeRateTestBase(TestCase):
    @staticmethod
    def make_rate(from_cur, to_cur, rate, date):
        return ExchangeRate.objects.create(
            from_cur=from_cur, to_cur=to_cur, rate=Decimal(str(rate)), date=date
        )


class MostRecentTests(ExchangeRateTestBase):
    def test_returns_1_when_no_rates_recorded_in_either_direction(self):
        self.assertEqual(ExchangeRate.most_recent("GBP", "EUR"), 1)

    def test_returns_direct_rate_when_recorded(self):
        self.make_rate("GBP", "EUR", "1.15000", timezone.now())
        self.assertEqual(ExchangeRate.most_recent("GBP", "EUR"), Decimal("1.15000"))

    def test_returns_latest_direct_rate_when_several_recorded(self):
        now = timezone.now()
        self.make_rate("GBP", "EUR", "1.10000", now - timedelta(days=10))
        self.make_rate("GBP", "EUR", "1.20000", now)
        self.assertEqual(ExchangeRate.most_recent("GBP", "EUR"), Decimal("1.20000"))

    def test_returns_inverted_rate_when_only_reverse_direction_recorded(self):
        self.make_rate("EUR", "GBP", "0.87000", timezone.now())
        self.assertEqual(ExchangeRate.most_recent("GBP", "EUR"), 1 / Decimal("0.87000"))

    def test_prefers_direct_rate_over_inverted_when_both_directions_recorded(self):
        now = timezone.now()
        self.make_rate("GBP", "EUR", "1.15000", now)
        self.make_rate("EUR", "GBP", "0.87000", now)
        self.assertEqual(ExchangeRate.most_recent("GBP", "EUR"), Decimal("1.15000"))


class AtDateTests(ExchangeRateTestBase):
    def test_returns_1_when_no_rates_recorded(self):
        self.assertEqual(ExchangeRate.at_date(timezone.now(), "GBP", "EUR"), 1)

    def test_returns_rate_recorded_exactly_on_the_given_date(self):
        # date__lte is inclusive.
        now = timezone.now()
        self.make_rate("GBP", "EUR", "1.15000", now)
        self.assertEqual(ExchangeRate.at_date(now, "GBP", "EUR"), Decimal("1.15000"))

    def test_excludes_rates_recorded_after_the_given_date(self):
        now = timezone.now()
        self.make_rate("GBP", "EUR", "1.15000", now + timedelta(days=1))
        self.assertEqual(ExchangeRate.at_date(now, "GBP", "EUR"), 1)

    def test_returns_the_latest_rate_at_or_before_the_given_date(self):
        now = timezone.now()
        self.make_rate("GBP", "EUR", "1.10000", now - timedelta(days=30))
        self.make_rate("GBP", "EUR", "1.20000", now - timedelta(days=1))
        self.make_rate("GBP", "EUR", "1.30000", now + timedelta(days=1))

        self.assertEqual(ExchangeRate.at_date(now, "GBP", "EUR"), Decimal("1.20000"))

    def test_returns_inverted_rate_when_only_reverse_direction_recorded_at_or_before_date(self):
        now = timezone.now()
        self.make_rate("EUR", "GBP", "0.87000", now - timedelta(days=1))
        self.assertEqual(ExchangeRate.at_date(now, "GBP", "EUR"), 1 / Decimal("0.87000"))

    def test_ignores_reverse_direction_rate_recorded_after_the_given_date(self):
        now = timezone.now()
        self.make_rate("EUR", "GBP", "0.87000", now + timedelta(days=1))
        self.assertEqual(ExchangeRate.at_date(now, "GBP", "EUR"), 1)

    def test_prefers_direct_rate_over_inverted_when_both_directions_recorded(self):
        now = timezone.now()
        self.make_rate("GBP", "EUR", "1.15000", now)
        self.make_rate("EUR", "GBP", "0.87000", now)
        self.assertEqual(ExchangeRate.at_date(now, "GBP", "EUR"), Decimal("1.15000"))
