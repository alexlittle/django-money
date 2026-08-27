from django.test import TestCase

from money.models import Account, InvoiceTemplate, Tag


class AccountStrTests(TestCase):
    def test_str_returns_name(self):
        account = Account.objects.create(name="Current Account", currency="GBP")
        self.assertEqual(str(account), "Current Account")


class TagStrTests(TestCase):
    def test_str_returns_name_when_no_category(self):
        tag = Tag.objects.create(name="Rent")
        self.assertEqual(str(tag), "Rent")

    def test_str_prefixes_category_when_present(self):
        tag = Tag.objects.create(name="Rent", category="house")
        self.assertEqual(str(tag), "house: Rent")


class InvoiceTemplateStrTests(TestCase):
    def test_str_shows_name_and_debit_breakdown(self):
        template = InvoiceTemplate.objects.create(
            name="Standard",
            debit_ex_alv=100,
            debit_alv=24,
            debit_total=124,
        )
        self.assertEqual(str(template), "Standard - 100 + 24 = 124")
