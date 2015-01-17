from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.utils import timezone

from money.models import Account

# Create your views here.


def home_view(request):
    accounts = Account.objects.filter(current=True)
    return render_to_response('money/home.html',
                              {'accounts': accounts},
                              context_instance=RequestContext(request))