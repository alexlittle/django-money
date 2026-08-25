from datetime import timedelta

from django.conf import settings
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone

from money.context_processors import (
    base_currency,
    get_accounting_periods,
    tags_menu,
)
from money.models import AccountingPeriod, Tag


class ContextProcessorTestBase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")


class BaseCurrencyTests(ContextProcessorTestBase):
    def test_returns_settings_value(self):
        context = base_currency(self.request)
        self.assertEqual(context, {"BASE_CURRENCY": settings.BASE_CURRENCY})

    @override_settings(BASE_CURRENCY="EUR")
    def test_reflects_overridden_setting(self):
        context = base_currency(self.request)
        self.assertEqual(context["BASE_CURRENCY"], "EUR")

    @override_settings(BASE_CURRENCY="GBP")
    def test_only_one_key_returned(self):
        context = base_currency(self.request)
        self.assertEqual(list(context.keys()), ["BASE_CURRENCY"])


class SeededAccountingPeriodTests(ContextProcessorTestBase):
    """Behaviour against the quarters created by money/migrations/0010.

    These run with the migrated table untouched, so they break if the
    data migration changes.
    """

    SEEDED_COUNT = 21
    NEWEST_TITLE = "2024 Q4"
    OLDEST_TITLE = "2019 Q4"

    def test_migration_seeded_the_expected_number_of_quarters(self):
        self.assertEqual(AccountingPeriod.objects.count(), self.SEEDED_COUNT)

    def test_all_seeded_quarters_are_active(self):
        self.assertFalse(AccountingPeriod.objects.filter(active=False).exists())

    def test_all_seeded_quarters_appear_in_the_context(self):
        context = get_accounting_periods(self.request)
        self.assertEqual(len(context["ACCOUNTING_PERIODS"]), self.SEEDED_COUNT)

    def test_seeded_quarters_are_newest_first(self):
        periods = list(get_accounting_periods(self.request)["ACCOUNTING_PERIODS"])
        self.assertEqual(periods[0].title, self.NEWEST_TITLE)
        self.assertEqual(periods[-1].title, self.OLDEST_TITLE)

    def test_seeded_quarters_are_fully_sorted_descending(self):
        periods = list(get_accounting_periods(self.request)["ACCOUNTING_PERIODS"])
        start_dates = [p.start_date for p in periods]
        self.assertEqual(start_dates, sorted(start_dates, reverse=True))


class GetAccountingPeriodsTests(ContextProcessorTestBase):
    """Filtering and ordering, isolated from the migration's seed data."""

    def setUp(self):
        super().setUp()
        # The 0010 data migration seeds 21 quarters. Clear them so each
        # test below asserts against only the rows it creates itself.
        # TestCase wraps this in a transaction, so nothing leaks out.
        AccountingPeriod.objects.all().delete()

    @staticmethod
    def make_period(title, start_date, active=True):
        return AccountingPeriod.objects.create(
            title=title,
            start_date=start_date,
            end_date=start_date + timedelta(days=89),
            active=active,
        )

    def test_returns_empty_when_no_periods(self):
        context = get_accounting_periods(self.request)
        self.assertEqual(list(context["ACCOUNTING_PERIODS"]), [])

    def test_excludes_inactive_periods(self):
        now = timezone.now()
        active = self.make_period("Active", now - timedelta(days=1), active=True)
        self.make_period("Inactive", now - timedelta(days=1), active=False)

        context = get_accounting_periods(self.request)
        self.assertEqual(list(context["ACCOUNTING_PERIODS"]), [active])

    def test_excludes_periods_starting_in_the_future(self):
        now = timezone.now()
        current = self.make_period("Current", now - timedelta(days=30))
        self.make_period("Future", now + timedelta(days=30))

        context = get_accounting_periods(self.request)
        self.assertEqual(list(context["ACCOUNTING_PERIODS"]), [current])

    def test_includes_period_starting_exactly_now(self):
        # start_date__lte is inclusive, so a period starting "now" counts.
        period = self.make_period("Right now", timezone.now())

        context = get_accounting_periods(self.request)
        self.assertIn(period, context["ACCOUNTING_PERIODS"])

    def test_ordered_by_start_date_descending(self):
        now = timezone.now()
        oldest = self.make_period("Oldest", now - timedelta(days=900))
        middle = self.make_period("Middle", now - timedelta(days=500))
        newest = self.make_period("Newest", now - timedelta(days=100))

        context = get_accounting_periods(self.request)
        self.assertEqual(
            list(context["ACCOUNTING_PERIODS"]),
            [newest, middle, oldest],
        )

    def test_combined_filtering_and_ordering(self):
        now = timezone.now()
        self.make_period("Future active", now + timedelta(days=10))
        self.make_period("Past inactive", now - timedelta(days=10), active=False)
        older = self.make_period("Past active older", now - timedelta(days=400))
        newer = self.make_period("Past active newer", now - timedelta(days=20))

        context = get_accounting_periods(self.request)
        self.assertEqual(list(context["ACCOUNTING_PERIODS"]), [newer, older])


class TagsMenuTests(ContextProcessorTestBase):
    def setUp(self):
        super().setUp()
        Tag.objects.all().delete()

    @staticmethod
    def make_tag(name, category):
        # Adjust if Tag has other required fields.
        return Tag.objects.create(name=name, category=category)

    def test_returns_empty_list_when_no_tags(self):
        context = tags_menu(self.request)
        self.assertEqual(context["TAG_MENU"], [])

    def test_returns_list_of_dicts_with_category_key(self):
        self.make_tag("Rent", "housing")

        context = tags_menu(self.request)
        self.assertEqual(context["TAG_MENU"], [{"category": "housing"}])

    def test_deduplicates_categories(self):
        self.make_tag("Rent", "housing")
        self.make_tag("Mortgage", "housing")
        self.make_tag("Train", "travel")

        context = tags_menu(self.request)
        categories = sorted(item["category"] for item in context["TAG_MENU"])
        self.assertEqual(categories, ["housing", "travel"])

    def test_result_is_a_plain_list_not_a_queryset(self):
        self.make_tag("Rent", "housing")

        menu = tags_menu(self.request)["TAG_MENU"]
        self.assertIsInstance(menu, list)

    def test_blank_category_is_still_included(self):
        # Documents current behaviour: there is no filtering of empty
        # categories, so a blank one becomes a menu entry.
        self.make_tag("Uncategorised", "")

        context = tags_menu(self.request)
        self.assertEqual(context["TAG_MENU"], [{"category": ""}])


class ContextProcessorRegistrationTests(TestCase):
    def test_processors_are_registered_in_templates(self):
        configured = settings.TEMPLATES[0]["OPTIONS"]["context_processors"]
        for path in (
            "money.context_processors.base_currency",
            "money.context_processors.get_accounting_periods",
            "money.context_processors.tags_menu",
        ):
            self.assertIn(path, configured)
