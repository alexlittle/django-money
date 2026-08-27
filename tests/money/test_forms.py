import datetime

from dateutil.relativedelta import relativedelta
from django.test import TestCase

from money.forms import InvoicesForm, set_due_date, set_title
from money.models import InvoiceTemplate


class SetDueDateTests(TestCase):
    def test_falls_on_the_2nd_of_the_month(self):
        self.assertEqual(set_due_date().day, 2)

    def test_is_in_the_month_after_now(self):
        expected = datetime.datetime.now() + relativedelta(months=1)
        due = set_due_date()
        self.assertEqual((due.year, due.month), (expected.year, expected.month))


class SetTitleTests(TestCase):
    def test_includes_next_months_service_fee_wording(self):
        expected = datetime.datetime.now() + relativedelta(months=1)
        self.assertEqual(
            set_title(), f"Palvelupaketti {expected.month}/{expected.year} (service fee)"
        )


class InvoicesFormTestBase(TestCase):
    @staticmethod
    def make_template(name="Standard", active=True):
        return InvoiceTemplate.objects.create(
            name=name, debit_ex_alv=100, debit_alv=24, debit_total=124, active=active
        )


class InvoicesFormTests(InvoicesFormTestBase):
    def test_valid_with_all_fields_supplied(self):
        template = self.make_template()
        form = InvoicesForm(
            data={
                "issue_date": "01.01.2026",
                "due_date": "02.02.2026",
                "title": "Invoice title",
                "ref_nos": "1001",
                "send_to": [template.id],
            }
        )
        self.assertTrue(form.is_valid())

    def test_invalid_when_required_fields_are_missing(self):
        form = InvoicesForm(data={})
        self.assertFalse(form.is_valid())
        for field in ("issue_date", "due_date", "title", "ref_nos", "send_to"):
            self.assertIn(field, form.errors)

    def test_send_to_queryset_only_offers_active_templates(self):
        active = self.make_template(name="Active", active=True)
        self.make_template(name="Inactive", active=False)

        form = InvoicesForm()

        self.assertEqual(list(form.fields["send_to"].queryset), [active])

    def test_invalid_when_send_to_references_an_inactive_template(self):
        inactive = self.make_template(name="Inactive", active=False)
        form = InvoicesForm(
            data={
                "issue_date": "01.01.2026",
                "due_date": "02.02.2026",
                "title": "Invoice title",
                "ref_nos": "1001",
                "send_to": [inactive.id],
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("send_to", form.errors)
