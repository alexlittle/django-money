from django import forms
from django.contrib.admin.sites import AdminSite
from django.contrib.admin.widgets import AdminSplitDateTime
from django.contrib.auth.models import User
from django.db import models as db_models
from django.test import RequestFactory, TestCase

from money import admin
from money.admin import (
    AccountAdmin,
    AccountingPeriodAdmin,
    ExchangeRateAdmin,
    InvoiceTemplateAdmin,
    RegularPaymentAdmin,
    TagAdmin,
    TransactionAdmin,
    TransactionTagAdmin,
    TransactionTagsInline,
    ValuationAdmin,
)
from money.models import (
    AccountingPeriod,
    ExchangeRate,
    InvoiceTemplate,
    RegularPayment,
    Transaction,
    TransactionTag,
    Valuation,
)


class DecimalFieldOverridesConstantTests(TestCase):
    def test_maps_decimal_field_to_a_text_input_widget(self):
        override = admin.DECIMAL_FIELD_OVERRIDES[db_models.DecimalField]
        self.assertIs(override["widget"], forms.TextInput)


class AdminFormWidgetTestBase(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.request = RequestFactory().get("/admin/")
        self.request.user = User.objects.create_superuser("admin", "admin@example.com", "password")

    def get_widgets(self, admin_class, model, field_names):
        admin_instance = admin_class(model, self.site)
        form_class = admin_instance.get_form(self.request)
        return {name: form_class.base_fields[name].widget for name in field_names}


class DecimalFieldsUseTextInputTests(AdminFormWidgetTestBase):
    def test_exchange_rate_admin_rate_field_uses_text_input(self):
        widgets = self.get_widgets(ExchangeRateAdmin, ExchangeRate, ["rate"])
        self.assertIsInstance(widgets["rate"], forms.TextInput)

    def test_regular_payment_admin_decimal_fields_use_text_input(self):
        widgets = self.get_widgets(RegularPaymentAdmin, RegularPayment, ["credit", "debit"])
        for widget in widgets.values():
            self.assertIsInstance(widget, forms.TextInput)

    def test_invoice_template_admin_decimal_fields_use_text_input(self):
        widgets = self.get_widgets(
            InvoiceTemplateAdmin,
            InvoiceTemplate,
            ["debit_ex_alv", "debit_alv", "debit_total", "deposit_held"],
        )
        for widget in widgets.values():
            self.assertIsInstance(widget, forms.TextInput)

    def test_transaction_admin_decimal_fields_use_text_input(self):
        widgets = self.get_widgets(
            TransactionAdmin,
            Transaction,
            ["credit", "debit", "sales_tax_charged", "sales_tax_paid", "sales_tax_rate"],
        )
        for widget in widgets.values():
            self.assertIsInstance(widget, forms.TextInput)

    def test_valuation_admin_decimal_fields_use_text_input(self):
        widgets = self.get_widgets(ValuationAdmin, Valuation, ["value", "value_per_month"])
        for widget in widgets.values():
            self.assertIsInstance(widget, forms.TextInput)

    def test_transaction_tag_admin_decimal_fields_use_text_input(self):
        widgets = self.get_widgets(
            TransactionTagAdmin, TransactionTag, ["allocation_credit", "allocation_debit"]
        )
        for widget in widgets.values():
            self.assertIsInstance(widget, forms.TextInput)

    def test_transaction_tags_inline_decimal_fields_use_text_input(self):
        inline = TransactionTagsInline(Transaction, self.site)
        formset_class = inline.get_formset(self.request)
        for field_name in ("allocation_credit", "allocation_debit"):
            widget = formset_class.form.base_fields[field_name].widget
            self.assertIsInstance(widget, forms.TextInput)


class AdminsWithoutDecimalFieldsAreUnaffectedTests(TestCase):
    # Account, Tag and AccountingPeriod have no DecimalFields, so their
    # admins should keep the default (empty) formfield_overrides rather
    # than picking up DECIMAL_FIELD_OVERRIDES.
    def test_account_admin_has_no_formfield_overrides(self):
        self.assertEqual(AccountAdmin.formfield_overrides, {})

    def test_tag_admin_has_no_formfield_overrides(self):
        self.assertEqual(TagAdmin.formfield_overrides, {})

    def test_accounting_period_admin_has_no_formfield_overrides(self):
        self.assertEqual(AccountingPeriodAdmin.formfield_overrides, {})

    def test_accounting_period_admin_form_keeps_default_date_widget(self):
        site = AdminSite()
        request = RequestFactory().get("/admin/")
        request.user = User.objects.create_superuser("admin2", "admin2@example.com", "password")
        admin_instance = AccountingPeriodAdmin(AccountingPeriod, site)
        form_class = admin_instance.get_form(request)
        # start_date is a DateTimeField, not a DecimalField, so it should
        # keep the admin's usual split date/time widget rather than being
        # swapped to a plain TextInput by DECIMAL_FIELD_OVERRIDES.
        self.assertIsInstance(form_class.base_fields["start_date"].widget, AdminSplitDateTime)
