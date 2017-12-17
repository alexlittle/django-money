
import datetime

from django.conf import settings
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.db.models import Sum, Max
from django.shortcuts import render
from django.template import RequestContext
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from money.models import Account, Transaction, Valuation, RegularPayment

def home_view(request):
    update_regular_payments()
    
    cash_accounts = []
    for k,v in settings.CURRENCIES_AVAILABLE:
        currency = {}
        currency['currency'] = k
        currency['account'] = Account.objects.filter(active=True, type='cash', currency=k).order_by('name')        
        cash_accounts.append(currency)
    
    invest_accounts = []
    for k,v in settings.CURRENCIES_AVAILABLE:
        currency = {}
        currency['currency'] = k
        currency['account'] = Account.objects.filter(active=True, type='invest', currency=k).order_by('name')        
        invest_accounts.append(currency) 
     
        
    return render(request, 'money/home.html',
                              {'cash_accounts': cash_accounts,
                               'invest_accounts': invest_accounts
                               })
    
def account_view(request, account_id):
    account = Account.objects.get(pk=account_id)
    trans = Transaction.objects.filter(account=account).order_by('-date')
    
    paginator = Paginator(trans, 100)
    
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    
    try:
        transactions = paginator.page(page)
    except (EmptyPage, InvalidPage):
        transactions = paginator.page(paginator.num_pages)
    
    return render(request,'money/account.html',
                              {'account': account,
                               'page': transactions, })
    
def update_regular_payments():
    payments = RegularPayment.objects.filter(next_date__lte=timezone.now())
    for rp in payments:
        # add to transactions
        transaction = Transaction(account=rp.account, payment_type=rp.payment_type, credit=rp.credit, debit = rp.debit, description=rp.description )
        print transaction
        transaction.save()
        # update regular payment
        next_date = rp.next_date + datetime.timedelta(days=31)
        rp.next_date = next_date
        rp.save()
    return