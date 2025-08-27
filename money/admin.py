from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from money.models import Account, ExchangeRate, RegularPayment, \
    Tag, Transaction, Valuation, TransactionTag, AccountingPeriod, InvoiceTemplate


# Register your models here.
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'currency', 'type', 'order')


class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ('from_cur', 'to_cur', 'date', 'rate')


class RegularPaymentAdmin(admin.ModelAdmin):
    list_display = ('account', 'description', 'credit', 'debit',
                    'next_date', 'end_date', 'payment_type')


class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'name')

class InvoiceTemplateAdmin(admin.ModelAdmin):
    list_display = ( 'name', 'description', 'active', 'debit_ex_alv', 'debit_alv', 'debit_total', 'deposit_held')

class TransactionTagAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'tag')


class TransactionTagsInline(admin.TabularInline):
    model = TransactionTag


class TransactionAdmin(admin.ModelAdmin):
    list_display = ('account', 'payment_type', 'date', 'credit', 'debit', 'on_statement', 'description', 'tags',
                    'pdf_receipt')
    search_fields = ['description']

    inlines = [
        TransactionTagsInline,
    ]

    def tags(self, obj):
        return list(Tag.objects.filter(transactiontag__transaction=obj).values_list("name", flat=True))

    def pdf_receipt(self, obj):
        if not obj.file.name and obj.credit > 0 and obj.sales_tax_rate > 0:
            return format_html("<a href='%s'>Receipt</a>" % reverse('money:transaction_receipt', args=(obj.id, )))


class ValuationAdmin(admin.ModelAdmin):
    list_display = ('account', 'date', 'value', 'value_per_month')


class AccountingPeriodAdmin(admin.ModelAdmin):
    list_display = ('start_date', 'end_date', 'title', 'active')


admin.site.register(Account, AccountAdmin)
admin.site.register(ExchangeRate, ExchangeRateAdmin)
admin.site.register(RegularPayment, RegularPaymentAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(InvoiceTemplate, InvoiceTemplateAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Valuation, ValuationAdmin)
admin.site.register(TransactionTag, TransactionTagAdmin)
admin.site.register(AccountingPeriod, AccountingPeriodAdmin)
