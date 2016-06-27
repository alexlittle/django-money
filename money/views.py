
import datetime

from django.db.models import Sum, Max
from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.utils import timezone

from money.models import Account, Transaction, Valuation, RegularPayment

# Create your views here.


def home_view(request):
    update_regular_payments()
    
    balances_gbp = Transaction.objects.filter(account__active=True, account__type='cash', account__currency='GBP').order_by('account__name').values('account').annotate(total_credit=Sum("credit"), total_debit=Sum("debit"))
    total_gbp = 0
    for b in balances_gbp:
        b['balance'] = b['total_credit'] - b['total_debit']
        b['account'] = Account.objects.get(pk=b['account'])
        total_gbp += b['balance']
      
      
      
    accs_gbp_invest = Account.objects.filter(active=True, type='invest', currency='GBP').order_by('name')
    total_gbp_invest = 0
    balances_gbp_invest = []
    for b in accs_gbp_invest:
        # get most recent valuation
        v_tmp = Valuation.objects.filter(account=b).aggregate(date=Max('date'))
        if v_tmp['date'] is not None:
            valuation = Valuation.objects.get(account=b, date=v_tmp['date'])
            acc = {}
            acc['account'] = b
            acc['balance'] = valuation.value
            acc['date'] = v_tmp['date']
            balances_gbp_invest.append(acc)
            total_gbp_invest += valuation.value
     
    accs_eur_invest = Account.objects.filter(active=True, type='invest', currency='EUR').order_by('name')
    total_eur_invest = 0
    balances_eur_invest = []
    for b in accs_eur_invest:
        # get most recent valuation
        v_tmp = Valuation.objects.filter(account=b).aggregate(date=Max('date'))
        if v_tmp['date'] is not None:
            valuation = Valuation.objects.get(account=b, date=v_tmp['date'])
            acc = {}
            acc['account'] = b
            acc['balance'] = valuation.value
            acc['date'] = v_tmp['date']
            balances_eur_invest.append(acc)
            total_eur_invest += valuation.value
             
    balances_eur = Transaction.objects.filter(account__active=True, account__type='cash', account__currency='EUR').order_by('account__name').values('account').annotate(total_credit=Sum("credit"), total_debit=Sum("debit"))
    total_eur = 0
    for b in balances_eur:
        b['balance'] = b['total_credit'] - b['total_debit']
        b['account'] = Account.objects.get(pk=b['account'])
        total_eur += b['balance']
     
    pensions_gbp = Account.objects.filter(type='pension',active=True, currency='GBP').order_by('name')
       
    return render_to_response('money/home.html',
                              {'balances_gbp': balances_gbp,
                               'total_gbp': total_gbp,
                               'balances_gbp_invest': balances_gbp_invest,
                               'total_gbp_invest': total_gbp_invest,
                               'balances_eur_invest': balances_eur_invest,
                               'total_eur_invest': total_eur_invest,
                               'balances_eur': balances_eur,
                               'total_eur': total_eur,
                               'pensions': pensions_gbp,},
                              context_instance=RequestContext(request))
    
def account_view(request, account_id):
    account = Account.objects.get(pk=account_id)
    transactions = Transaction.objects.filter(account=account).order_by('-date')[:100]
    return render_to_response('money/account.html',
                              {'account': account,
                               'transactions': transactions, },
                              context_instance=RequestContext(request))
    
def update_regular_payments():
    payments = RegularPayment.objects.filter(next_date__lte=timezone.now())
    print payments
    for rp in payments:
        # add to transactions
        transaction = Transaction(account=rp.account, payment_type=rp.payment_type, credit=rp.credit, debit = rp.debit, description=rp.description )
        print transaction
        transaction.save()
        # update regularpayment
        next_date = rp.next_date + datetime.timedelta(days=31)
        rp.next_date = next_date
        rp.save()
        print next_date
    return