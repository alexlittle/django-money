from django.contrib import admin

from money.models import Account, ExchangeRate, RegularPayment, \
    Tag, Transaction, Valuation, TransactionTag


# Register your models here.
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'currency', 'type')


class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ('from_cur', 'to_cur', 'date', 'rate')


class RegularPaymentAdmin(admin.ModelAdmin):
    list_display = ('account', 'description', 'credit', 'debit',
                    'next_date', 'end_date', 'payment_type')


class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


class TransactionAdmin(admin.ModelAdmin):
    list_display = ('account', 'payment_type', 'date', 'credit',
                    'debit', 'on_statement', 'description')
    search_fields = ['description']


class ValuationAdmin(admin.ModelAdmin):
    list_display = ('account', 'date', 'value')


class TransactionTagAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'tag')


admin.site.register(Account, AccountAdmin)
admin.site.register(ExchangeRate, ExchangeRateAdmin)
admin.site.register(RegularPayment, RegularPaymentAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Valuation, ValuationAdmin)
admin.site.register(TransactionTag, TransactionTagAdmin)
