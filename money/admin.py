from django import forms
from django.contrib import admin
from django.db import models as db_models

from money.models import (
    Account,
    AccountingPeriod,
    ExchangeRate,
    InvoiceTemplate,
    RegularPayment,
    Tag,
    Transaction,
    TransactionTag,
    Valuation,
)

# Browser <input type="number"> widgets interpret decimal separators using the
# OS/browser locale, which can silently mangle amounts (e.g. dropping the
# fraction) when the machine's locale doesn't use "." for decimals. Use a
# plain text input for DecimalFields so entry doesn't depend on that locale.
DECIMAL_FIELD_OVERRIDES = {
    db_models.DecimalField: {"widget": forms.TextInput},
}


# Register your models here.
class AccountAdmin(admin.ModelAdmin):
    list_display = ("name", "active", "currency", "type", "order")


class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ("from_cur", "to_cur", "date", "rate")
    formfield_overrides = DECIMAL_FIELD_OVERRIDES


class RegularPaymentAdmin(admin.ModelAdmin):
    formfield_overrides = DECIMAL_FIELD_OVERRIDES
    list_display = (
        "account",
        "description",
        "credit",
        "debit",
        "next_date",
        "end_date",
        "payment_type",
    )


class TagAdmin(admin.ModelAdmin):
    list_display = ("id", "category", "name", "active")


class InvoiceTemplateAdmin(admin.ModelAdmin):
    formfield_overrides = DECIMAL_FIELD_OVERRIDES
    list_display = (
        "name",
        "description",
        "active",
        "debit_ex_alv",
        "debit_alv",
        "debit_total",
        "deposit_held",
    )


class TransactionTagAdmin(admin.ModelAdmin):
    formfield_overrides = DECIMAL_FIELD_OVERRIDES
    list_display = ("transaction", "tag")


class TransactionTagsInline(admin.TabularInline):
    model = TransactionTag
    formfield_overrides = DECIMAL_FIELD_OVERRIDES

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == "tag":
            kwargs["queryset"] = Tag.objects.filter(active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class TransactionAdmin(admin.ModelAdmin):
    formfield_overrides = DECIMAL_FIELD_OVERRIDES
    list_display = (
        "account",
        "payment_type",
        "date",
        "credit",
        "debit",
        "on_statement",
        "description",
        "tags",
    )
    search_fields = ["description"]

    inlines = [
        TransactionTagsInline,
    ]

    def tags(self, obj):
        return list(
            Tag.objects.filter(transactiontag__transaction=obj).values_list("name", flat=True)
        )


class ValuationAdmin(admin.ModelAdmin):
    formfield_overrides = DECIMAL_FIELD_OVERRIDES
    list_display = ("account", "date", "value", "value_per_month")


class AccountingPeriodAdmin(admin.ModelAdmin):
    list_display = ("start_date", "end_date", "title", "active")


admin.site.register(Account, AccountAdmin)
admin.site.register(ExchangeRate, ExchangeRateAdmin)
admin.site.register(RegularPayment, RegularPaymentAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(InvoiceTemplate, InvoiceTemplateAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Valuation, ValuationAdmin)
admin.site.register(TransactionTag, TransactionTagAdmin)
admin.site.register(AccountingPeriod, AccountingPeriodAdmin)
