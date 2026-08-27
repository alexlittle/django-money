import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from django.urls import reverse

from money.models import InvoiceTemplate

# See tests/money/test_views_receipt.py: PDFTemplateResponse shells out to
# the wkhtmltopdf binary, which isn't available in CI, so it's mocked here.
# INVOICE_ACCOUNT_NAME/IBAN/BIC and INVOICE_OUTPUT_DIR only exist in the
# untracked, personal config/local_settings.py - they aren't defined in
# config/settings.py or config/settings_ci.py, so these tests supply their
# own values via override_settings rather than depending on them existing.


class CreateInvoicesViewTestBase(TestCase):
    @staticmethod
    def make_template(name="Standard", active=True):
        return InvoiceTemplate.objects.create(
            name=name, debit_ex_alv=100, debit_alv=24, debit_total=124, active=active
        )


class CreateInvoicesViewGetTests(CreateInvoicesViewTestBase):
    def test_returns_200_and_uses_the_create_invoices_template(self):
        response = self.client.get(reverse("money:create_invoices"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "money/create_invoices.html")

    def test_form_offers_only_active_templates(self):
        active = self.make_template(name="Active", active=True)
        self.make_template(name="Inactive", active=False)

        response = self.client.get(reverse("money:create_invoices"))

        self.assertEqual(list(response.context["form"].fields["send_to"].queryset), [active])


class CreateInvoicesViewPostTests(CreateInvoicesViewTestBase):
    def setUp(self):
        self.output_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.output_dir.cleanup)
        self.settings_override = override_settings(
            INVOICE_OUTPUT_DIR=self.output_dir.name,
            INVOICE_ACCOUNT_NAME="Alex Little Consulting Services",
            INVOICE_ACCOUNT_IBAN="FI28 1199 3000 1051 66",
            INVOICE_ACCOUNT_BIC="NDEAFIHH",
        )
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)

    @patch("money.views.PDFTemplateResponse")
    def test_writes_a_pdf_named_from_due_date_template_and_ref_no(self, mock_pdf_response):
        mock_pdf_response.return_value = MagicMock(rendered_content=b"pdf-bytes")
        template = self.make_template(name="Kollektiivi")

        response = self.client.post(
            reverse("money:create_invoices"),
            data={
                "issue_date": "01.05.2026",
                "due_date": "15.06.2026",
                "title": "Invoice title",
                "ref_nos": "1001",
                "send_to": [template.id],
            },
        )

        self.assertRedirects(response, "/invoices/create/done/")
        expected_file = Path(self.output_dir.name) / "invoice-2026-06-kollektiivi-1001.pdf"
        self.assertTrue(expected_file.exists())
        self.assertEqual(expected_file.read_bytes(), b"pdf-bytes")

    @patch("money.views.PDFTemplateResponse")
    def test_passes_account_details_and_ref_through_to_the_template_context(
        self, mock_pdf_response
    ):
        mock_pdf_response.return_value = MagicMock(rendered_content=b"pdf-bytes")
        template = self.make_template(name="Kollektiivi")

        self.client.post(
            reverse("money:create_invoices"),
            data={
                "issue_date": "01.05.2026",
                "due_date": "15.06.2026",
                "title": "Invoice title",
                "ref_nos": "1001",
                "send_to": [template.id],
            },
        )

        _, kwargs = mock_pdf_response.call_args
        context = kwargs["context"]
        self.assertEqual(context["ref"], "1001")
        self.assertEqual(context["title"], "Invoice title")
        self.assertEqual(context["invoice_info"], template)
        self.assertEqual(context["acc_name"], "Alex Little Consulting Services")
        self.assertEqual(context["acc_iban"], "FI28 1199 3000 1051 66")
        self.assertEqual(context["acc_bic"], "NDEAFIHH")

    @patch("money.views.PDFTemplateResponse")
    def test_writes_one_pdf_per_selected_template_pairing_ref_nos_by_order(self, mock_pdf_response):
        mock_pdf_response.return_value = MagicMock(rendered_content=b"pdf-bytes")
        first = self.make_template(name="First")
        second = self.make_template(name="Second")

        self.client.post(
            reverse("money:create_invoices"),
            data={
                "issue_date": "01.05.2026",
                "due_date": "15.06.2026",
                "title": "Invoice title",
                "ref_nos": "1001,1002",
                "send_to": [first.id, second.id],
            },
        )

        # send_to is cleaned into a queryset ordered by primary key
        # (InvoiceTemplate has no Meta.ordering), not by selection order,
        # so ref_nos are paired to templates in pk order here.
        first_file = Path(self.output_dir.name) / "invoice-2026-06-first-1001.pdf"
        second_file = Path(self.output_dir.name) / "invoice-2026-06-second-1002.pdf"
        self.assertTrue(first_file.exists())
        self.assertTrue(second_file.exists())

    def test_invalid_form_does_not_redirect_or_write_files(self):
        response = self.client.post(reverse("money:create_invoices"), data={})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(Path(self.output_dir.name).iterdir()), [])
