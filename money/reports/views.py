import datetime
import dateutil.relativedelta

from django.db.models import Sum, Max
from django.shortcuts import render, render_to_response
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

    return render_to_response('money/reports/by_month.html',
                              {
                               'currency': currency,
                               'transactions': transactions},
                              context_instance=RequestContext(request))
    
def by_year_view(request,currency='GBP'):
    
    transactions = Transaction.objects.filter(account__currency=currency).exclude(payment_type='Transfer').\
                                        extra(select={'year': "EXTRACT(year FROM date)"}).\
                                        values('year').\
                                        annotate(sum_in=Sum('credit'),sum_out=Sum('debit')).\
                                        order_by('-year')
    
    balance = 0
    for b in transactions:
        b['balance'] = b['sum_in'] - b['sum_out']

    return render_to_response('money/reports/by_year.html',
                              {
                               'currency': currency,
                               'transactions': transactions},
                              context_instance=RequestContext(request))
    
    
def graph_view(request,currency='GBP'):
    
    now = datetime.datetime.now()
    tz = timezone.get_default_timezone()
    
    balances = []
    
    valuation_accounts = Valuation.objects.filter(account__type='invest').values_list('account_id').distinct()
    
    print valuation_accounts
    
    for i in range(96,-1,-1):
        balance = {} 
        old_date = now - dateutil.relativedelta.relativedelta(months=i)
        last_day = datetime.datetime(int(old_date.strftime("%Y")), int(old_date.strftime("%m")), 1, 23, 59, tzinfo=tz)\
                     + dateutil.relativedelta.relativedelta(day=1, months=+1, days=-1)
        
        # non valuation GBP accounts
        transactions_gbp = Transaction.objects.filter(account__currency='GBP',date__lte=last_day, account__type='cash').\
                                        exclude( account_id__in=valuation_accounts, payment_type='Transfer').\
                                        aggregate(sum_in=Sum('credit'),sum_out=Sum('debit'))
        non_valuation_gbp = transactions_gbp['sum_in']-transactions_gbp['sum_out'] 
        
        valuation_gbp = 0
        # valuation GBP accounts
        for va in valuation_accounts:
            v = Valuation.objects.filter(account_id=va, date__lte=last_day).aggregate(max=Max('date'))
            value = Valuation.objects.filter(account_id=va,date=v['max'])
            if value:
                valuation_gbp += value[0].value
        
        # non valuation EUR accounts
        transactions_eur = Transaction.objects.filter(account__currency='EUR',date__lte=last_day, account__type='cash').\
                                        exclude(account_id__in=valuation_accounts, payment_type='Transfer').\
                                        aggregate(sum_in=Sum('credit'),sum_out=Sum('debit'))
         
        non_valuation_eur = 0
        d = ExchangeRate.objects.filter(date__lte=last_day).order_by('-date')[:1]
        if d.count() > 0:
            ex_rate = d[0].rate
            non_valuation_eur = (transactions_eur['sum_in']-transactions_eur['sum_out']) * ex_rate
            print non_valuation_eur
                                            
        balance['date'] = last_day
        balance['total'] = non_valuation_gbp + valuation_gbp + non_valuation_eur
        balance['valuation_gbp'] = valuation_gbp
        balance['non_valuation_gbp'] = non_valuation_gbp
        balance['non_valuation_eur'] = non_valuation_eur
        
        balances.append(balance) 
                            
    
    return render_to_response('money/reports/graph.html',
                              {
                               'balances': balances},
                              context_instance=RequestContext(request))
    