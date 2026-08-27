from decimal import Decimal
from unittest.mock import patch

from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from money.models import Account, Transaction

# django-wkhtmltopdf's PDFTemplateResponse shells out to the wkhtmltopdf
# binary. It's installed on this machine but not in CI (see
# .github/workflows/workflow.yml), so these tests mock it out rather than
# actually invoking the subprocess - that keeps them fast and portable,
# and lets us assert on what the view asked it to render.


class TransactionReceiptViewTests(TestCase):
    @staticmethod
    def make_transaction():
        account = Account.objects.create(name="Test account", currency="GBP")
        return Transaction.objects.create(
            account=account,
            payment_type="Card",
            description="Test transaction",
            credit=Decimal("100"),
            date=timezone.now(),
        )

    @patch("money.views.PDFTemplateResponse")
    def test_renders_the_receipt_template_with_the_transaction_in_context(self, mock_pdf_response):
        mock_pdf_response.return_value = HttpResponse(b"pdf-bytes", content_type="application/pdf")
        transaction = self.make_transaction()

        response = self.client.get(reverse("money:transaction_receipt", args=[transaction.id]))

        self.assertEqual(response.status_code, 200)
        _, kwargs = mock_pdf_response.call_args
        self.assertEqual(kwargs["template"], "money/receipt.html")
        self.assertEqual(kwargs["context"]["transaction"], transaction)
        self.assertFalse(kwargs["show_content_in_browser"])

    @patch("money.views.PDFTemplateResponse")
    def test_filename_includes_the_transaction_date_and_id(self, mock_pdf_response):
        mock_pdf_response.return_value = HttpResponse(b"pdf-bytes", content_type="application/pdf")
        transaction = self.make_transaction()
        expected_date = transaction.date.strftime("%Y-%m-%d")

        self.client.get(reverse("money:transaction_receipt", args=[transaction.id]))

        _, kwargs = mock_pdf_response.call_args
        self.assertEqual(kwargs["filename"], f"{expected_date}-receipt-{transaction.id}.pdf")

    def test_raises_does_not_exist_for_unknown_transaction(self):
        with self.assertRaises(Transaction.DoesNotExist):
            self.client.get(reverse("money:transaction_receipt", args=[999999]))
