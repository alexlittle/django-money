import datetime
import os

from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.db import models
from django.db.models import Sum, Max, F
from django.utils import timezone


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
        ('cash', 'Cash'),
        ('invest', 'Investment'),
        ('property', 'Property'),
        ('pension', 'Pension')
    )

TAG_CATEGORIES = (
        ('travel', 'Travel'),
        ('house', 'House'),
        ('kollektiivi', 'Kollektiivi'),
        ('car', 'Car'),
        ('personal', 'Personal'),
        ('misc', 'Misc'),
        ('business', 'Business'),
        ('design', 'DesignShop'),
        ('rental', 'Rental'),
    )


class Account (models.Model):
    name = models.CharField(max_length=100, blank=False, null=False)
    active = models.BooleanField(blank=False, default=True)
    currency = models.CharField(max_length=3, choices=settings.CURRENCIES_AVAILABLE)
    type = models.CharField(max_length=100, choices=ACCOUNT_TYPES, default='cash')
    notes = models.TextField(blank=True, default=None, null=True)

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
    def get_balance_at_date(account, date, tag=None):
        if tag:
            trans_cred = Transaction.objects.filter(
                account=account,
                date__lte=date,
                transactiontag__tag__name=tag).annotate(
                    credit_percent=F("credit")*F("transactiontag__percent")/100
                    ).aggregate(credit_sum=Sum("credit_percent"))
            trans_deb = Transaction.objects.filter(
                account=account,
                date__lte=date,
                transactiontag__tag__name=tag).annotate(
                    debit_percent=F("debit")*F("transactiontag__percent")/100
                    ).aggregate(debit_sum=Sum("debit_percent"))
        else:
            trans_cred = Transaction.objects.filter(account=account, date__lte=date).aggregate(credit_sum=Sum("credit"))
            trans_deb = Transaction.objects.filter(account=account, date__lte=date).aggregate(debit_sum=Sum("debit"))

        if trans_deb['debit_sum'] is None and trans_cred['credit_sum'] is None:
            return 0
        elif trans_deb['debit_sum'] is None:
            return trans_cred['credit_sum']
        elif trans_cred['credit_sum'] is None:
            return trans_deb['debit_sum']
        else:
            return trans_cred['credit_sum'] - trans_deb['debit_sum']

    def get_valuation(self):
        v_tmp = Valuation.objects.filter(account=self, value__gt=0).aggregate(date=Max('date'))
        if v_tmp['date'] is not None:
            valuation = Valuation.objects.get(account=self, value__gt=0, date=v_tmp['date'])
            return valuation
        else:
            return None

    def get_monthly_valuation(self):
        v_tmp = Valuation.objects.filter(account=self, value_per_month__gt=0).aggregate(date=Max('date'))
        if v_tmp['date'] is not None:
            valuation = Valuation.objects.get(account=self, value_per_month__gt=0, date=v_tmp['date'])
            return valuation
        else:
            return None

    @staticmethod
    def get_valuation_at_date(account, date):
        v_tmp = Valuation.objects.filter(account=account, value__gt=0, date__lte=date).aggregate(date=Max('date'))
        if v_tmp['date'] is not None:
            valuation = Valuation.objects.get(account=account, value__gt=0, date=v_tmp['date'])
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
    def get_balance_base_currency_at_date(account, date, tag=None):
        if account.currency == settings.BASE_CURRENCY:
            return Account.get_balance_at_date(account, date, tag)
        else:
            rate = ExchangeRate.at_date(date, settings.BASE_CURRENCY, account.currency)
            balance = Account.get_balance_at_date(account, date, tag)
            if balance:
                return balance/rate
            else:
                return 0

    def get_valuation_base_currency(self):
        if self.currency == settings.BASE_CURRENCY:
            if self.get_valuation():
                return self.get_valuation().value
            else:
                return 0
        else:
            if self.get_valuation():
                rate = ExchangeRate.most_recent(settings.BASE_CURRENCY, self.currency)
                return self.get_valuation().value/rate
            else:
                return 0

    def get_monthly_valuation_base_currency(self):
        if self.currency == settings.BASE_CURRENCY:
            if self.get_monthly_valuation():
                return self.get_monthly_valuation().value_per_month
            else:
                return 0
        else:
            if self.get_monthly_valuation():
                rate = ExchangeRate.most_recent(settings.BASE_CURRENCY, self.currency)
                return self.get_monthly_valuation().value_per_month/rate
            else:
                return 0

    @staticmethod
    def get_valuation_base_currency_at_date(account, date):
        if account.currency == settings.BASE_CURRENCY:
            if Account.get_valuation_at_date(account, date):
                return Account.get_valuation_at_date(account, date).value
            else:
                return 0
        else:
            rate = ExchangeRate.at_date(
                date, settings.BASE_CURRENCY, account.currency)
            if Account.get_valuation_at_date(account, date):
                return Account.get_valuation_at_date(account, date).value/rate
            else:
                return 0

    @staticmethod
    def get_paid_in_base_currency_at_date(account, date):
        if account.currency == settings.BASE_CURRENCY:
            credit = Transaction.objects.filter(account=account, date__lte=date).aggregate(paid_in=Sum("credit"))
            if credit['paid_in']:
                return credit['paid_in']
            else:
                return 0
        else:
            rate = ExchangeRate.at_date(date, settings.BASE_CURRENCY, account.currency)
            credit = Transaction.objects.filter(account=account, date__lte=date).aggregate(paid_in=Sum("credit"))
            if credit['paid_in']:
                return credit['paid_in']/rate
            else:
                return 0

    @staticmethod
    def get_balance_total(type, currency):
        accs = Account.objects.filter(active=True, type=type, currency=currency)
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
        accs = Account.objects.filter(active=True, type=type, currency=currency)
        total = 0
        for acc in accs:
            if acc.get_balance_base_currency():
                total += acc.get_balance_base_currency()
        return total

    @staticmethod
    def get_valuation_total(type, currency):
        accs = Account.objects.filter(active=True, type=type, currency=currency)
        total = 0
        for acc in accs:
            if acc.get_valuation() != 0:
                total += acc.get_valuation().value
        return total

    @staticmethod
    def get_valuation_base_currency_total(type, currency):
        accs = Account.objects.filter(active=True, type=type, currency=currency)
        total = 0
        for acc in accs:
            total += acc.get_valuation_base_currency()
        return total

    @staticmethod
    def get_val_base_currency_total(type):
        accs = Account.objects.filter(active=True, type=type)
        total = 0
        for acc in accs:
            total += acc.get_valuation_base_currency()
        return total

    @staticmethod
    def get_monthly_val_base_currency_total(type):
        accs = Account.objects.filter(active=True, type=type)
        total = 0
        for acc in accs:
            total += acc.get_monthly_valuation_base_currency()
        return total

    def get_compound_interest(self, years):
        start_date = datetime.datetime.now() - relativedelta(years=years)
        start_acc_value = Account.get_valuation_at_date(self, start_date)
        end_acc_value = Account.get_valuation_at_date(self, datetime.datetime.now())
        if not start_acc_value or not end_acc_value:
            return 0
        start_valuation = start_acc_value.value
        end_valuation = end_acc_value.value

        rate = ((float(end_valuation)/float(start_valuation))**(1/float(years)) - 1)*100
        return rate

class ExchangeRate (models.Model):
    from_cur = models.CharField(
        max_length=3, choices=settings.CURRENCIES_AVAILABLE)
    to_cur = models.CharField(
        max_length=3, choices=settings.CURRENCIES_AVAILABLE)
    date = models.DateTimeField(default=timezone.now)
    rate = models.DecimalField(decimal_places=5, max_digits=20)

    @staticmethod
    def most_recent(from_currency, to_currency):
        tmp_date = ExchangeRate.objects.filter(
            from_cur=from_currency, to_cur=to_currency).aggregate(date=Max('date'))
        if tmp_date['date'] is not None:
            rate = ExchangeRate.objects.get(
                from_cur=from_currency, to_cur=to_currency, date=tmp_date['date'])
            return rate.rate
        tmp_date = ExchangeRate.objects.filter(
            from_cur=to_currency, to_cur=from_currency).aggregate(date=Max('date'))
        if tmp_date['date'] is not None:
            rate = ExchangeRate.objects.get(
                from_cur=to_currency, to_cur=from_currency, date=tmp_date['date'])
            return 1/rate.rate
        return 1

    @staticmethod
    def at_date(date, from_currency, to_currency):

        tmp_date = ExchangeRate.objects.filter(
            from_cur=from_currency, to_cur=to_currency, date__lte=date).aggregate(date=Max('date'))
        if tmp_date['date'] is not None:
            rate = ExchangeRate.objects.get(
                from_cur=from_currency, to_cur=to_currency, date=tmp_date['date'])
            return rate.rate
        tmp_date = ExchangeRate.objects.filter(
            from_cur=to_currency, to_cur=from_currency, date__lte=date).aggregate(date=Max('date'))
        if tmp_date['date'] is not None:
            rate = ExchangeRate.objects.get(
                from_cur=to_currency, to_cur=from_currency, date=tmp_date['date'])
            return 1/rate.rate
        return 1


class RegularPayment(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    description = models.CharField(max_length=100, blank=False, null=False)
    credit = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    debit = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    next_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(default=timezone.now)
    payment_type = models.CharField(max_length=15, choices=PAYMENT_TYPES)


class Tag(models.Model):
    name = models.CharField(max_length=100, blank=False, null=False)
    category = models.CharField(max_length=100, choices=TAG_CATEGORIES, blank=True, null=True)

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        if self.category:
            return self.category + ": " + self.name
        else:
            return self.name


class Transaction(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    payment_type = models.CharField(max_length=15, choices=PAYMENT_TYPES)
    date = models.DateTimeField(default=timezone.now)
    credit = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    debit = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    on_statement = models.BooleanField(blank=False, default=False)
    description = models.CharField(max_length=100, blank=False, null=False)
    sales_tax_charged = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    sales_tax_paid = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    sales_tax_rate = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    file = models.FileField(upload_to="transaction", blank=True, default=None)

    def filename(self):
        return os.path.basename(self.file.name)

    def get_excl_sales_tax(self):
        return self.credit - self.sales_tax_charged

    def get_credit_in_base_currency(self):
        if settings.BASE_CURRENCY == self.account.currency:
            return self.credit
        else:
            ex_rate = ExchangeRate.at_date(self.date, self.account.currency, settings.BASE_CURRENCY)
            return self.credit/(1/ex_rate)

    def get_debit_in_base_currency(self):
        if settings.BASE_CURRENCY == self.account.currency:
            return self.debit
        else:
            ex_rate = ExchangeRate.at_date(self.date, self.account.currency, settings.BASE_CURRENCY)
            return self.debit/(1/ex_rate)

class Valuation(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    value = models.DecimalField(decimal_places=2, max_digits=20)
    value_per_month = models.DecimalField(decimal_places=2, max_digits=20, default=0)


class TransactionTag(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    allocation_credit = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    allocation_debit = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    description = models.CharField(max_length=200, blank=True, null=True, default=None)

    def get_credit_in_base_currency(self):
        if settings.BASE_CURRENCY == self.transaction.account.currency:
            return self.allocation_credit
        else:
            ex_rate = ExchangeRate.at_date(self.transaction.date, self.transaction.account.currency, settings.BASE_CURRENCY)
            return self.allocation_credit/(1/ex_rate)

    def get_debit_in_base_currency(self):
        if settings.BASE_CURRENCY == self.transaction.account.currency:
            return self.allocation_debit
        else:
            ex_rate = ExchangeRate.at_date(self.transaction.date, self.transaction.account.currency, settings.BASE_CURRENCY)
            return self.allocation_debit/(1/ex_rate)

class AccountingPeriod(models.Model):
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(default=timezone.now)
    active = models.BooleanField(blank=False, default=True)
    title = models.CharField(max_length=100, blank=False, null=False)


class InvoiceTemplate(models.Model):
    name = models.CharField(max_length=100, blank=False, null=False)
    description = models.TextField(blank=True, default=None, null=True)
    active = models.BooleanField(blank=False, default=True)
    debit_ex_alv = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    debit_alv = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    debit_total = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    deposit_held = models.DecimalField(decimal_places=2, max_digits=20, default=0)

    def __str__(self):
        return "{name} - {ex_alv} + {alv} = {total}".format(name=self.name, ex_alv=self.debit_ex_alv, alv=self.debit_alv, total=self.debit_total)
