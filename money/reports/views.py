import datetime

from django.db.models import Sum, Max
from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.utils import timezone

from money.models import Account, Transaction, Valuation, RegularPayment

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