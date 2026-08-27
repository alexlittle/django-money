from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from money.models import Account, ExchangeRate, Tag, Transaction, TransactionTag


class TransactionTestBase(TestCase):
    @staticmethod
    def make_account(currency="GBP", name="Test account"):
        return Account.objects.create(name=name, currency=currency)

    @staticmethod
    def make_transaction(account, credit=0, debit=0, sales_tax_charged=0, date=None):
        return Transaction.objects.create(
            account=account,
            payment_type="Card",
            description="Test transaction",
            credit=Decimal(str(credit)),
            debit=Decimal(str(debit)),
            sales_tax_charged=Decimal(str(sales_tax_charged)),
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


class GetExclSalesTaxTests(TransactionTestBase):
    def test_subtracts_sales_tax_charged_from_credit(self):
        account = self.make_account()
        transaction = self.make_transaction(account, credit=120, sales_tax_charged=20)
        self.assertEqual(transaction.get_excl_sales_tax(), Decimal("100"))

    def test_zero_sales_tax_leaves_credit_unchanged(self):
        account = self.make_account()
        transaction = self.make_transaction(account, credit=100)
        self.assertEqual(transaction.get_excl_sales_tax(), Decimal("100"))


class FilenameTests(TransactionTestBase):
    def test_returns_empty_string_when_no_file_attached(self):
        account = self.make_account()
        transaction = self.make_transaction(account)
        self.assertEqual(transaction.filename(), "")

    def test_strips_directory_from_the_stored_path(self):
        account = self.make_account()
        transaction = self.make_transaction(account)
        transaction.file.name = "transaction/2024/receipt.pdf"
        self.assertEqual(transaction.filename(), "receipt.pdf")


class TransactionBaseCurrencyConversionTests(TransactionTestBase):
    def test_get_credit_in_base_currency_returns_credit_directly_for_base_currency(self):
        account = self.make_account(currency="GBP")
        transaction = self.make_transaction(account, credit=100)
        self.assertEqual(transaction.get_credit_in_base_currency(), Decimal("100"))

    def test_get_credit_in_base_currency_converts_for_non_base_currency(self):
        account = self.make_account(currency="EUR")
        transaction = self.make_transaction(account, credit=115)
        self.make_rate("GBP", "EUR", "1.15", date=transaction.date)

        self.assertEqual(transaction.get_credit_in_base_currency(), Decimal("100"))

    def test_get_credit_in_base_currency_uses_rate_at_transaction_date(self):
        account = self.make_account(currency="EUR")
        now = timezone.now()
        transaction = self.make_transaction(account, credit=110, date=now - timedelta(days=10))
        self.make_rate("GBP", "EUR", "1.10", date=now - timedelta(days=20))
        self.make_rate("GBP", "EUR", "1.20", date=now - timedelta(days=1))

        self.assertEqual(transaction.get_credit_in_base_currency(), Decimal("100"))

    def test_get_debit_in_base_currency_returns_debit_directly_for_base_currency(self):
        account = self.make_account(currency="GBP")
        transaction = self.make_transaction(account, debit=100)
        self.assertEqual(transaction.get_debit_in_base_currency(), Decimal("100"))

    def test_get_debit_in_base_currency_converts_for_non_base_currency(self):
        account = self.make_account(currency="EUR")
        transaction = self.make_transaction(account, debit=115)
        self.make_rate("GBP", "EUR", "1.15", date=transaction.date)

        self.assertEqual(transaction.get_debit_in_base_currency(), Decimal("100"))


class TransactionTagTestBase(TransactionTestBase):
    @staticmethod
    def make_tag(name="Rent", category="house"):
        return Tag.objects.create(name=name, category=category)

    @staticmethod
    def make_transaction_tag(transaction, tag, allocation_credit=0, allocation_debit=0):
        return TransactionTag.objects.create(
            transaction=transaction,
            tag=tag,
            allocation_credit=Decimal(str(allocation_credit)),
            allocation_debit=Decimal(str(allocation_debit)),
        )


class TransactionTagBaseCurrencyConversionTests(TransactionTagTestBase):
    def test_get_credit_in_base_currency_returns_allocation_directly_for_base_currency(self):
        account = self.make_account(currency="GBP")
        transaction = self.make_transaction(account, credit=100)
        tag = self.make_tag()
        transaction_tag = self.make_transaction_tag(transaction, tag, allocation_credit=40)

        self.assertEqual(transaction_tag.get_credit_in_base_currency(), Decimal("40"))

    def test_get_credit_in_base_currency_converts_for_non_base_currency(self):
        account = self.make_account(currency="EUR")
        transaction = self.make_transaction(account, credit=115)
        self.make_rate("GBP", "EUR", "1.15", date=transaction.date)
        tag = self.make_tag()
        transaction_tag = self.make_transaction_tag(transaction, tag, allocation_credit=115)

        self.assertEqual(transaction_tag.get_credit_in_base_currency(), Decimal("100"))

    def test_get_credit_in_base_currency_uses_rate_at_the_transactions_date(self):
        account = self.make_account(currency="EUR")
        now = timezone.now()
        transaction = self.make_transaction(account, credit=110, date=now - timedelta(days=10))
        self.make_rate("GBP", "EUR", "1.10", date=now - timedelta(days=20))
        self.make_rate("GBP", "EUR", "1.20", date=now - timedelta(days=1))
        tag = self.make_tag()
        transaction_tag = self.make_transaction_tag(transaction, tag, allocation_credit=110)

        self.assertEqual(transaction_tag.get_credit_in_base_currency(), Decimal("100"))

    def test_get_debit_in_base_currency_returns_allocation_directly_for_base_currency(self):
        account = self.make_account(currency="GBP")
        transaction = self.make_transaction(account, debit=100)
        tag = self.make_tag()
        transaction_tag = self.make_transaction_tag(transaction, tag, allocation_debit=40)

        self.assertEqual(transaction_tag.get_debit_in_base_currency(), Decimal("40"))

    def test_get_debit_in_base_currency_converts_for_non_base_currency(self):
        account = self.make_account(currency="EUR")
        transaction = self.make_transaction(account, debit=115)
        self.make_rate("GBP", "EUR", "1.15", date=transaction.date)
        tag = self.make_tag()
        transaction_tag = self.make_transaction_tag(transaction, tag, allocation_debit=115)

        self.assertEqual(transaction_tag.get_debit_in_base_currency(), Decimal("100"))
