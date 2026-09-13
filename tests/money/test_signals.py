from decimal import Decimal

from django.db.models.signals import pre_save
from django.test import TestCase

from money.models import Account, Tag, Transaction, TransactionTag


class SignalsAreConnectedTests(TestCase):
    # Regression test: money/signals.py defines these pre_save handlers, but
    # they only get connected because MoneyAppConfig.ready() imports the
    # module for its side effects. That import has been silently dropped
    # before (see commits 4620076 and b625fd9), leaving the handlers defined
    # but never wired up, with nothing failing loudly to catch it.
    def test_check_allocation_added_is_connected_to_transactiontag_pre_save(self):
        sync_receivers, _ = pre_save._live_receivers(sender=TransactionTag)
        names = [r.__name__ for r in sync_receivers]
        self.assertIn("check_allocation_added", names)

    def test_calculate_sales_tax_is_connected_to_transaction_pre_save(self):
        sync_receivers, _ = pre_save._live_receivers(sender=Transaction)
        names = [r.__name__ for r in sync_receivers]
        self.assertIn("calculate_sales_tax", names)


class CheckAllocationAddedTests(TestCase):
    @staticmethod
    def make_account():
        return Account.objects.create(name="Test account", currency="GBP")

    @staticmethod
    def make_transaction(account, credit=0, debit=0):
        return Transaction.objects.create(
            account=account,
            payment_type="Card",
            description="Test transaction",
            credit=Decimal(str(credit)),
            debit=Decimal(str(debit)),
        )

    def test_tagging_a_transaction_auto_fills_allocation_from_transaction_amounts(self):
        account = self.make_account()
        transaction = self.make_transaction(account, credit=42, debit=0)
        tag = Tag.objects.create(name="Food")

        transaction_tag = TransactionTag.objects.create(transaction=transaction, tag=tag)

        self.assertEqual(transaction_tag.allocation_credit, Decimal("42"))
        self.assertEqual(transaction_tag.allocation_debit, Decimal("0"))

    def test_explicit_allocation_amounts_are_not_overwritten(self):
        account = self.make_account()
        transaction = self.make_transaction(account, credit=100, debit=0)
        tag = Tag.objects.create(name="Food")

        transaction_tag = TransactionTag.objects.create(
            transaction=transaction,
            tag=tag,
            allocation_credit=Decimal("30"),
            allocation_debit=Decimal("0"),
        )

        self.assertEqual(transaction_tag.allocation_credit, Decimal("30"))
