from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.utils import timezone
# Create your views here.


def home_view(request):
    return render_to_response('money/home.html',
                              {},
                              context_instance=RequestContext(request))