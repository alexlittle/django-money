
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
    
    def __unicode__(self):
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
        
    def get_valuation(self):
        v_tmp = Valuation.objects.filter(account=self).aggregate(date=Max('date'))
        if v_tmp['date'] is not None:
            valuation = Valuation.objects.get(account=self, date=v_tmp['date'])
            return valuation
        else:
            return 0
    
    
    
class ExchangeRate (models.Model):
    from_cur = models.CharField(max_length=3,choices=settings.CURRENCIES_AVAILABLE)
    to_cur = models.CharField(max_length=3,choices=settings.CURRENCIES_AVAILABLE)
    date = models.DateTimeField(default=timezone.now)
    rate = models.DecimalField(decimal_places=5, max_digits=20)
   
class RegularPayment(models.Model):
    account = models.ForeignKey(Account)
    description = models.CharField(max_length=100, blank=False, null=False)
    credit = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    debit = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    next_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(default=timezone.now)
    payment_type = models.CharField(max_length=15,choices=PAYMENT_TYPES)
    
class Tag(models.Model):
    name = models.CharField(max_length=100, blank=False, null=False)
    
    
class Transaction(models.Model):
    account = models.ForeignKey(Account)
    payment_type = models.CharField(max_length=15,choices=PAYMENT_TYPES)
    date = models.DateTimeField(default=timezone.now)
    credit = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    debit = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    on_statement = models.BooleanField(blank=False, default=False)
    description = models.CharField(max_length=100, blank=False, null=False)
    
class Valuation(models.Model):
    account = models.ForeignKey(Account)
    date = models.DateTimeField(default=timezone.now)
    value = models.DecimalField(decimal_places=2, max_digits=20)
    
class TransactionTag(models.Model):
    transaction = models.ForeignKey(Transaction)
    tag = models.ForeignKey(Tag)
    