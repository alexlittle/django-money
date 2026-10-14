import datetime
from contextlib import redirect_stdout
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from money.models import Account, Tag, Transaction, TransactionTag

IN_RANGE = datetime.datetime(2025, 8, 1, 12, 0, tzinfo=datetime.UTC)


class InterestIncomeCommandTests(TestCase):
    def setUp(self):
        self.interest_tag = Tag.objects.create(name="interest")

    @staticmethod
    def make_account(name):
        return Account.objects.create(name=name, currency="GBP")

    def make_transaction(self, account, credit, date=IN_RANGE, tag=None):
        transaction = Transaction.objects.create(
            account=account,
            payment_type="Card",
            description="Test transaction",
            credit=Decimal(str(credit)),
            debit=Decimal("0"),
            date=date,
        )
        TransactionTag.objects.create(transaction=transaction, tag=tag or self.interest_tag)
        return transaction

    @staticmethod
    def run_command():
        out = StringIO()
        with redirect_stdout(out):
            call_command("interest_income")
        return out.getvalue().splitlines()

    def test_no_output_when_no_transactions(self):
        self.assertEqual(self.run_command(), [])

    def test_sums_interest_per_account(self):
        savings = self.make_account("Savings")
        self.make_transaction(savings, "10.50")
        self.make_transaction(savings, "4.25")

        self.assertEqual(self.run_command(), ["Savings 14.75"])

    def test_outputs_accounts_ordered_by_name(self):
        self.make_transaction(self.make_account("Zeta"), 1)
        self.make_transaction(self.make_account("Alpha"), 2)

        lines = self.run_command()

        self.assertEqual([line.split()[0] for line in lines], ["Alpha", "Zeta"])

    def test_ignores_transactions_without_interest_tag(self):
        account = self.make_account("Savings")
        other = Tag.objects.create(name="salary")
        self.make_transaction(account, 100, tag=other)
        self.make_transaction(account, 5)

        self.assertEqual(self.run_command(), ["Savings 5.00"])

    def test_ignores_transactions_before_start_date(self):
        account = self.make_account("Savings")
        self.make_transaction(
            account, 50, date=timezone.make_aware(datetime.datetime(2025, 4, 5, 23, 0))
        )

        self.assertEqual(self.run_command(), [])

    def test_ignores_transactions_on_or_after_end_date(self):
        account = self.make_account("Savings")
        self.make_transaction(
            account, 50, date=timezone.make_aware(datetime.datetime(2026, 4, 6, 12, 0))
        )

        self.assertEqual(self.run_command(), [])

    def test_includes_transaction_on_start_date(self):
        account = self.make_account("Savings")
        self.make_transaction(
            account, 7, date=timezone.make_aware(datetime.datetime(2025, 4, 6, 12, 0))
        )

        self.assertEqual(self.run_command(), ["Savings 7.00"])
