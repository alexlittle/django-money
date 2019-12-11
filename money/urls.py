# money/urls.py
from django.conf import settings
from django.conf.urls import include, url

from money import views as money_views

urlpatterns = [
    url(r'^$', money_views.home_view, name="money_home"),
    url(r'^account/(?P<account_id>\d+)/$', money_views.account_view, name="money_account"),
    url(r'^reports/', include('money.reports.urls')),
    url(r'^transaction/(?P<transaction_id>\d+)/toggle/$', money_views.transaction_toggle, name="transaction_toggle"),
]
