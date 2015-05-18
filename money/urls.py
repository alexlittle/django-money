# money/urls.py
from django.conf import settings
from django.conf.urls import patterns, include, url


urlpatterns = patterns('',

    url(r'^$', 'money.views.home_view', name="money_home"),
    url(r'^account/(?P<account_id>\d+)/$', 'money.views.account_view', name="money_account"),
    
    url(r'^reports/', include('money.reports.urls')),
)
