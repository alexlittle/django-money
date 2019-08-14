import os
from django.conf import settings
from django.db import models
from django.db.models import Sum, Max
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

PAYMENT_TYPES = (
        ('Visa', 'Visa'),
        ('Transfer', 'Transfer'),
        ('Paid in', 'Paid in'),
        ('Pay', 'Pay'),
        ('Standing Order', 'Standing Order'),
        ('Cheque', 'Cheque'),
        ('Interest', 'Interest'),
        ('Switch', 'Switch'),
        ('Cashpoint', 'Cashpoint'),
        ('Direct Debit', 'Direct Debit'),
        ('Mastercard', 'Mastercard'),
    )

ACCOUNT_TYPES = (
        ('cash','Cash'),
        ('invest','Investment'),
        ('property', 'Property'),
        ('pension', 'Pension')
    )

class Account (models.Model):
    name = models.CharField(max_length=100, blank=False, null=False)
    active = models.BooleanField(blank=False, default=True)
    currency = models.CharField(max_length=3,choices=settings.CURRENCIES_AVAILABLE)
    type = models.CharField(max_length=100, choices=ACCOUNT_TYPES, default='cash')
    
    def __str__(self):
        return self.name
    
    def on_statement(self):
        trans_cred = Transaction.objects.filter(account=self, on_statement=True).aggregate(Sum("credit"))
        trans_deb = Transaction.objects.filter(account=self, on_statement=True).aggregate(Sum("debit"))
        if trans_deb['debit__sum'] is None:
            return trans_cred['credit__sum']
        return trans_cred['credit__sum'] - trans_deb['debit__sum']
    
    def get_balance(self):
        trans_cred = Transaction.objects.filter(account=self).aggregate(Sum("credit"))
        trans_deb = Transaction.objects.filter(account=self).aggregate(Sum("debit"))
        if trans_deb['debit__sum'] is None:
            return trans_cred['credit__sum']
        return trans_cred['credit__sum'] - trans_deb['debit__sum']
     
    @staticmethod   
    def get_balance_at_date(account, date):
        trans_cred = Transaction.objects.filter(account=account, date__lte=date).aggregate(Sum("credit"))
        trans_deb = Transaction.objects.filter(account=account, date__lte=date).aggregate(Sum("debit"))
        if trans_deb['debit__sum'] is None:
            return trans_cred['credit__sum']
        return trans_cred['credit__sum'] - trans_deb['debit__sum']
    
    def get_valuation(self):
        v_tmp = Valuation.objects.filter(account=self).aggregate(date=Max('date'))
        if v_tmp['date'] is not None:
            valuation = Valuation.objects.get(account=self, date=v_tmp['date'])
            return valuation
        else:
            return None
        
    @staticmethod     
    def get_valuation_at_date(account, date):
        v_tmp = Valuation.objects.filter(account=account, date__lte=date).aggregate(date=Max('date'))
        if v_tmp['date'] is not None:
            valuation = Valuation.objects.get(account=account, date=v_tmp['date'])
            return valuation
        else:
            return None
    
    def get_balance_base_currency(self):
        if self.currency == settings.BASE_CURRENCY:
            return self.get_balance()
        else:
            rate = ExchangeRate.most_recent(settings.BASE_CURRENCY, self.currency)
            return self.get_balance()/rate
    
    @staticmethod   
    def get_balance_base_currency_at_date(account, date):
        if account.currency == settings.BASE_CURRENCY:
            return Account.get_balance_at_date(account, date)
        else:
            rate = ExchangeRate.at_date(date, settings.BASE_CURRENCY, account.currency)
            if Account.get_balance_at_date(account, date):
                return Account.get_balance_at_date(account, date)/rate
            else:
                return 0
        
    def get_valuation_base_currency(self):
        if self.currency == settings.BASE_CURRENCY:
            return self.get_valuation().value
        else:
            rate = ExchangeRate.most_recent(settings.BASE_CURRENCY, self.currency)
            return self.get_valuation().value/rate
     
    @staticmethod  
    def get_valuation_base_currency_at_date(account, date):
        if account.currency == settings.BASE_CURRENCY:
            if Account.get_valuation_at_date(account, date):
                return Account.get_valuation_at_date(account, date).value
            else:
                return 0
        else:
            rate = ExchangeRate.at_date(date, settings.BASE_CURRENCY, account.currency)
            if Account.get_valuation_at_date(account, date):
                return Account.get_valuation_at_date(account, date).value/rate
            else:
                return 0
    
    @staticmethod
    def get_balance_total(type, currency):
        accs = Account.objects.filter(active=True,type=type, currency=currency)
        total = 0
        for acc in accs:
            if acc.get_balance():
                total += acc.get_balance()
        return total
        
      
    @staticmethod
    def get_on_statment_total(type, currency):
        accs = Account.objects.filter(active=True, type=type, currency=currency)
        total = 0
        for acc in accs:
            if acc.on_statement() is not None:
                total += acc.on_statement()
        return total  
     
    @staticmethod
    def get_balance_base_currency_total(type, currency):
        accs = Account.objects.filter(active=True,type=type, currency=currency)
        total = 0
        for acc in accs:
            if acc.get_balance_base_currency():
                total += acc.get_balance_base_currency()
        return total   
    
    @staticmethod
    def get_valuation_total(type, currency):
        accs = Account.objects.filter(active=True,type=type, currency=currency)
        total = 0
        for acc in accs:
            if acc.get_valuation() is not 0:
                total += acc.get_valuation().value
        return total
    
    @staticmethod
    def get_valuation_base_currency_total(type, currency):
        accs = Account.objects.filter(active=True,type=type, currency=currency)
        total = 0
        for acc in accs:
            total += acc.get_valuation_base_currency()
        return total
    
    @staticmethod
    def get_val_base_currency_total(type):
        accs = Account.objects.filter(active=True,type=type)
        total = 0
        for acc in accs:
            total += acc.get_valuation_base_currency()
        return total
            
class ExchangeRate (models.Model):
    from_cur = models.CharField(max_length=3,choices=settings.CURRENCIES_AVAILABLE)
    to_cur = models.CharField(max_length=3,choices=settings.CURRENCIES_AVAILABLE)
    date = models.DateTimeField(default=timezone.now)
    rate = models.DecimalField(decimal_places=5, max_digits=20)
    
    @staticmethod
    def most_recent(from_currency, to_currency):
        tmp_date = ExchangeRate.objects.filter(from_cur=from_currency, to_cur=to_currency).aggregate(date=Max('date'))
        if tmp_date['date'] is not None:
            rate = ExchangeRate.objects.get(from_cur=from_currency, to_cur=to_currency, date=tmp_date['date'])
            return rate.rate
        tmp_date = ExchangeRate.objects.filter(from_cur=to_currency, to_cur=from_currency).aggregate(date=Max('date'))
        if tmp_date['date'] is not None:
            rate = ExchangeRate.objects.get(from_cur=to_currency, to_cur=from_currency, date=tmp_date['date'])
            return 1/rate.rate   
        return 1  
   
    @staticmethod
    def at_date(date, from_currency, to_currency):
        
        tmp_date = ExchangeRate.objects.filter(from_cur=from_currency, to_cur=to_currency, date__lte=date).aggregate(date=Max('date'))
        if tmp_date['date'] is not None:
            rate = ExchangeRate.objects.get(from_cur=from_currency, to_cur=to_currency, date=tmp_date['date'])
            return rate.rate
        tmp_date = ExchangeRate.objects.filter(from_cur=to_currency, to_cur=from_currency, date__lte=date).aggregate(date=Max('date'))
        if tmp_date['date'] is not None:
            rate = ExchangeRate.objects.get(from_cur=to_currency, to_cur=from_currency, date=tmp_date['date'])
            return 1/rate.rate   
        return 1 
   
class RegularPayment(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    description = models.CharField(max_length=100, blank=False, null=False)
    credit = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    debit = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    next_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(default=timezone.now)
    payment_type = models.CharField(max_length=15,choices=PAYMENT_TYPES)
    
class Tag(models.Model):
    name = models.CharField(max_length=100, blank=False, null=False)
    
    
class Transaction(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    payment_type = models.CharField(max_length=15,choices=PAYMENT_TYPES)
    date = models.DateTimeField(default=timezone.now)
    credit = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    debit = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    on_statement = models.BooleanField(blank=False, default=False)
    description = models.CharField(max_length=100, blank=False, null=False)
    sales_tax_charged = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    sales_tax_paid = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    file = models.FileField(upload_to="transaction", blank=True, default=None)
    
    def filename(self):
        return os.path.basename(self.file.name)
    
class Valuation(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    date = models.DateTimeField(default=timezone.now)
    value = models.DecimalField(decimal_places=2, max_digits=20)
    
class TransactionTag(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    