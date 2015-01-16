from django.db import models
from django.utils import timezone

CURRENCY_TYPES = (
        ('GBP', 'GBP'),
        ('EUR', 'EUR'),
    )

PAYMENT_TYPES = (
        ('VISA', 'Visa'),
        ('TRANSFER', 'Transfer'),
        ('PAID_IN', 'Paid in'),
        ('PAY', 'Pay'),
    )

# Create your models here.

class Account (models.Model):
    name = models.CharField(max_length=100, blank=False, null=False)
    include = models.BooleanField(blank=False, default=True)
    current = models.BooleanField(blank=False, default=True)
    currency = models.CharField(max_length=3,choices=CURRENCY_TYPES)
    pension = models.BooleanField(blank=False, default=False)
    
class ExchangeRate (models.Model):
    from_cur = models.CharField(max_length=3,choices=CURRENCY_TYPES)
    to_cur = models.CharField(max_length=3,choices=CURRENCY_TYPES)
    date = models.DateTimeField(default=timezone.now)
    rate = models.DecimalField(decimal_places=2, max_digits=20)
   
class RegularPayment(models.Model):
    account = models.ForeignKey(Account)
    description = models.CharField(max_length=100, blank=False, null=False)
    credit = models.DecimalField(decimal_places=2, max_digits=20)
    debit = models.DecimalField(decimal_places=2, max_digits=20)
    next_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(default=timezone.now)
    payment_type = models.CharField(max_length=15,choices=PAYMENT_TYPES)
    
class Tag(models.Model):
    name = models.CharField(max_length=100, blank=False, null=False)
    
    
class Transaction(models.Model):
    account = models.ForeignKey(Account)
    payment_type = models.CharField(max_length=15,choices=PAYMENT_TYPES)
    date = models.DateTimeField(default=timezone.now)
    credit = models.DecimalField(decimal_places=2, max_digits=20)
    debit = models.DecimalField(decimal_places=2, max_digits=20)
    on_statement = models.BooleanField(blank=False, default=False)
    description = models.CharField(max_length=100, blank=False, null=False)
    
class Valuation(models.Model):
    account = models.ForeignKey(Account)
    date = models.DateTimeField(default=timezone.now)
    value = models.DecimalField(decimal_places=2, max_digits=20)
    
class TransactionTag(models.Model):
    transaction = models.ForeignKey(Transaction)
    tag = models.ForeignKey(Tag)
    