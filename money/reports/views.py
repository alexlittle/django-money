import datetime
import dateutil.relativedelta

from django.db.models import Sum, Max
from django.shortcuts import render
from django.template import RequestContext
from django.utils import timezone

from money.models import Account, Transaction, Valuation, RegularPayment, ExchangeRate

# Create your views here.


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
    
    
def graph_view(request,currency='GBP'):
    
    now = datetime.datetime.now()
    tz = timezone.get_default_timezone()
    
    balances = []
    
    valuation_gbp_accounts = Valuation.objects.filter(account__type='invest', account__currency='GBP').values_list('account_id').distinct()
    valuation_eur_accounts = Valuation.objects.filter(account__type='invest', account__currency='EUR').values_list('account_id').distinct()

    for i in range(96,-1,-1):
        balance = {} 
        old_date = now - dateutil.relativedelta.relativedelta(months=i)
        last_day = datetime.datetime(int(old_date.strftime("%Y")), int(old_date.strftime("%m")), 1, 23, 59, tzinfo=tz)\
                     + dateutil.relativedelta.relativedelta(day=1, months=+1, days=-1)
        
        d = ExchangeRate.objects.filter(date__lte=last_day).order_by('-date')[:1]
        ex_rate = d[0].rate
        
        # non valuation GBP accounts
        transactions_gbp = Transaction.objects.filter(account__currency='GBP',date__lte=last_day, account__type='cash').\
                                        exclude( account_id__in=valuation_gbp_accounts, payment_type='Transfer').\
                                        aggregate(sum_in=Sum('credit'),sum_out=Sum('debit'))
        non_valuation_gbp = transactions_gbp['sum_in']-transactions_gbp['sum_out'] 
        
        valuation_gbp = 0
        # valuation GBP accounts
        for va in valuation_gbp_accounts:
            v = Valuation.objects.filter(account_id=va, date__lte=last_day).aggregate(max=Max('date'))
            value = Valuation.objects.filter(account_id=va,date=v['max'])
            if value:
                valuation_gbp += value[0].value
        
        
        valuation_eur = 0
        # valuation EUR accounts
        for va in valuation_eur_accounts:
            v = Valuation.objects.filter(account_id=va, date__lte=last_day).aggregate(max=Max('date'))
            value = Valuation.objects.filter(account_id=va,date=v['max'])
            if value:
                valuation_eur += (value[0].value) * ex_rate
                
        # non valuation EUR accounts
        transactions_eur = Transaction.objects.filter(account__currency='EUR',date__lte=last_day, account__type='cash').\
                                        exclude(account_id__in=valuation_eur_accounts, payment_type='Transfer').\
                                        aggregate(sum_in=Sum('credit'),sum_out=Sum('debit'))
        
        non_valuation_eur = 0 
        if transactions_eur['sum_in'] is not None:
            non_valuation_eur = (transactions_eur['sum_in']-transactions_eur['sum_out']) * ex_rate
                                            
        balance['date'] = last_day
        balance['total'] = non_valuation_gbp + valuation_gbp + non_valuation_eur + valuation_eur
        balance['valuation_gbp'] = valuation_gbp
        balance['valuation_eur'] = valuation_eur
        balance['non_valuation_gbp'] = non_valuation_gbp
        balance['non_valuation_eur'] = non_valuation_eur
        
        balances.append(balance) 
                            
    
    return render(request,'money/reports/graph.html',
                              {
                               'balances': balances})
    