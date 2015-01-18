
from django.db.models import Sum, Max
from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.utils import timezone

from money.models import Account, Transaction, Valuation

# Create your views here.


def home_view(request):
    balances_gbp = Transaction.objects.filter(account__current=True, account__include=True, account__currency='GBP').order_by('account__name').values('account').annotate(total_credit=Sum("credit"), total_debit=Sum("debit"))
    total_gbp = 0
    for b in balances_gbp:
        b['balance'] = b['total_credit'] - b['total_debit']
        b['account'] = Account.objects.get(pk=b['account'])
        total_gbp += b['balance']
      
      
      
    accs_invest = Account.objects.filter(current=True, include=False, currency='GBP').order_by('name')
    total_invest = 0
    balances_invest = []
    for b in accs_invest:
        # get most recent valuation
        v_tmp = Valuation.objects.filter(account=b).aggregate(date=Max('date'))
        valuation = Valuation.objects.get(account=b, date=v_tmp['date'])
        acc = {}
        acc['account'] = b
        acc['balance'] = valuation.value
        acc['date'] = v_tmp['date']
        balances_invest.append(acc)
        total_invest += valuation.value
          
    balances_eur = Transaction.objects.filter(account__current=True, account__include=True, account__currency='EUR').order_by('account__name').values('account').annotate(total_credit=Sum("credit"), total_debit=Sum("debit"))
    total_eur = 0
    for b in balances_eur:
        b['balance'] = b['total_credit'] - b['total_debit']
        b['account'] = Account.objects.get(pk=b['account'])
        total_eur += b['balance']
        
    return render_to_response('money/home.html',
                              {'balances_gbp': balances_gbp,
                               'total_gbp': total_gbp,
                               'balances_invest': balances_invest,
                               'total_invest': total_invest,
                               'balances_eur': balances_eur,
                               'total_eur': total_eur,},
                              context_instance=RequestContext(request))
    
def account_view(request, account_id):
    account = Account.objects.get(pk=account_id)
    transactions = Transaction.objects.filter(account=account).order_by('-date')[:100]
    return render_to_response('money/account.html',
                              {'account': account,
                               'transactions': transactions, },
                              context_instance=RequestContext(request))