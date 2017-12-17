import datetime
import dateutil.relativedelta

from django.conf import settings
from django.db.models import Sum, Max
from django.shortcuts import render
from django.template import RequestContext
from django.utils import timezone

from money.models import Account, Transaction, Valuation, RegularPayment, ExchangeRate


def by_month_view(request,currency='GBP'):
    
    transactions = Transaction.objects.filter(account__currency=currency).exclude(payment_type='Transfer').\
                                        extra(select={'year': "EXTRACT(year FROM date)", 'month': "EXTRACT(month FROM date)"}).\
                                        values('year','month').\
                                        annotate(sum_in=Sum('credit'),sum_out=Sum('debit')).\
                                        order_by('-year','-month')
    
    balance = 0
    for b in transactions:
        b['balance'] = b['sum_in'] - b['sum_out']

    return render(request,'money/reports/by_month.html',
                              {
                               'currency': currency,
                               'transactions': transactions})
    
def by_year_view(request,currency='GBP'):
    
    transactions = Transaction.objects.filter(account__currency=currency).exclude(payment_type='Transfer').\
                                        extra(select={'year': "EXTRACT(year FROM date)"}).\
                                        values('year').\
                                        annotate(sum_in=Sum('credit'),sum_out=Sum('debit')).\
                                        order_by('-year')
    
    balance = 0
    for b in transactions:
        b['balance'] = b['sum_in'] - b['sum_out']

    return render(request,'money/reports/by_year.html',
                              {
                               'currency': currency,
                               'transactions': transactions})
    
    
def graph_view(request):
    
    now = datetime.datetime.now()
    tz = timezone.get_default_timezone()
    
    balances = []

    for i in range(96,-1,-1):
        balance = {} 
        old_date = now - dateutil.relativedelta.relativedelta(months=i)
        last_day = datetime.datetime(int(old_date.strftime("%Y")), int(old_date.strftime("%m")), 1, 23, 59, tzinfo=tz)\
                     + dateutil.relativedelta.relativedelta(day=1, months=+1, days=-1)
        
        cash_total = 0
        accs = Account.objects.filter(active=True, type='cash') 
        for acc in accs:
            if Account.get_balance_base_currency_at_date(acc,last_day):
                cash_total += Account.get_balance_base_currency_at_date(acc,last_day)
        
        invest_total = 0 
        accs = Account.objects.filter(active=True, type='invest') 
        for acc in accs:
            if Account.get_valuation_base_currency_at_date(acc,last_day):
                invest_total += Account.get_valuation_base_currency_at_date(acc,last_day)
                                            
        balance['date'] = last_day
        balance['total'] = cash_total + invest_total
        balance['cash'] = cash_total
        balance['invest'] = invest_total
        
        balances.append(balance) 
                            
    
    return render(request,'money/reports/graph.html',
                              {'balances': balances})
    