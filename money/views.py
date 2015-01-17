
from django.db.models import Sum
from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.utils import timezone

from money.models import Account, Transaction

# Create your views here.


def home_view(request):
    balances = Transaction.objects.filter(account__current=True).values('account').annotate(total_credit=Sum("credit"), total_debit=Sum("debit"))
    for b in balances:
        b['balance'] = b['total_credit'] - b['total_debit']
        b['account'] = Account.objects.get(pk=b['account'])
    return render_to_response('money/home.html',
                              {'balances': balances},
                              context_instance=RequestContext(request))