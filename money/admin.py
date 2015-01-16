from django.contrib import admin

from money.models import Account, ExchangeRate, RegularPayment, Tag, Transaction, Valuation, TransactionTag

# Register your models here.


class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'include', 'current', 'currency', 'pension')

class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ('name', 'include', 'current', 'currency', 'pension')
    
class RegularPaymentAdmin(admin.ModelAdmin):
    list_display = ('name', 'include', 'current', 'currency', 'pension')
    
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'include', 'current', 'currency', 'pension')
    
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('name', 'include', 'current', 'currency', 'pension')
    
class ValuationAdmin(admin.ModelAdmin):
    list_display = ('name', 'include', 'current', 'currency', 'pension')
    
class TransactionTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'include', 'current', 'currency', 'pension')
                 
admin.site.register(Account,AccountAdmin)
admin.site.register(ExchangeRate,ExchangeRateAdmin)
admin.site.register(RegularPayment,RegularPaymentAdmin)
admin.site.register(Tag,TagAdmin)
admin.site.register(Transaction,TransactionAdmin)
admin.site.register(Valuation,ValuationAdmin)
admin.site.register(TransactionTag,TransactionTagAdmin)