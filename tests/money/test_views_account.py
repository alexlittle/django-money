from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from money.models import Account, Transaction


class AccountViewTestBase(TestCase):
    @staticmethod
    def make_account(currency="GBP", name="Test account"):
        return Account.objects.create(name=name, currency=currency)

    @staticmethod
    def make_transaction(account, credit=0, date=None):
        return Transaction.objects.create(
            account=account,
            payment_type="Card",
            description="Test transaction",
            credit=Decimal(str(credit)),
            date=date or timezone.now(),
        )


class AccountViewTests(AccountViewTestBase):
    def test_returns_200_and_uses_account_template(self):
        account = self.make_account()
        response = self.client.get(reverse("money:money_account", args=[account.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "money/account.html")

    def test_raises_does_not_exist_for_unknown_account(self):
        # Known gap: the view calls Account.objects.get() directly instead
        # of get_object_or_404, so an unknown id surfaces as an unhandled
        # DoesNotExist (a 500 in production) rather than a 404 page.
        with self.assertRaises(Account.DoesNotExist):
            self.client.get(reverse("money:money_account", args=[999999]))

    def test_lists_only_this_accounts_transactions_newest_first(self):
        account = self.make_account(name="A")
        other = self.make_account(name="B")
        now = timezone.now()
        older = self.make_transaction(account, credit=10, date=now - timedelta(days=1))
        newer = self.make_transaction(account, credit=20, date=now)
        self.make_transaction(other, credit=999, date=now)

        response = self.client.get(reverse("money:money_account", args=[account.id]))

        self.assertEqual(list(response.context["page"].object_list), [newer, older])


class AccountViewPaginationTests(AccountViewTestBase):
    def setUp(self):
        self.account = self.make_account()
        now = timezone.now()
        # 250 transactions -> 3 pages at 100 per page.
        self.transactions = [
            self.make_transaction(self.account, credit=i, date=now - timedelta(minutes=i))
            for i in range(250)
        ]

    def test_defaults_to_page_1(self):
        response = self.client.get(reverse("money:money_account", args=[self.account.id]))
        self.assertEqual(response.context["page"].number, 1)
        self.assertEqual(len(response.context["page"].object_list), 100)

    def test_requests_a_specific_page(self):
        response = self.client.get(
            reverse("money:money_account", args=[self.account.id]), {"page": "2"}
        )
        self.assertEqual(response.context["page"].number, 2)

    def test_non_integer_page_falls_back_to_page_1(self):
        response = self.client.get(
            reverse("money:money_account", args=[self.account.id]), {"page": "notanumber"}
        )
        self.assertEqual(response.context["page"].number, 1)

    def test_out_of_range_page_falls_back_to_last_page(self):
        response = self.client.get(
            reverse("money:money_account", args=[self.account.id]), {"page": "999"}
        )
        self.assertEqual(response.context["page"].number, 3)


class TransactionToggleViewTests(AccountViewTestBase):
    def test_toggles_on_statement_from_false_to_true(self):
        account = self.make_account()
        transaction = self.make_transaction(account, credit=10)
        self.assertFalse(transaction.on_statement)

        self.client.get(reverse("money:transaction_toggle", args=[transaction.id]))

        transaction.refresh_from_db()
        self.assertTrue(transaction.on_statement)

    def test_toggles_on_statement_from_true_to_false(self):
        account = self.make_account()
        transaction = self.make_transaction(account, credit=10)
        transaction.on_statement = True
        transaction.save()

        self.client.get(reverse("money:transaction_toggle", args=[transaction.id]))

        transaction.refresh_from_db()
        self.assertFalse(transaction.on_statement)

    def test_redirects_to_the_transactions_account_page(self):
        account = self.make_account()
        transaction = self.make_transaction(account, credit=10)

        response = self.client.get(reverse("money:transaction_toggle", args=[transaction.id]))

        self.assertRedirects(response, reverse("money:money_account", args=[account.id]))
