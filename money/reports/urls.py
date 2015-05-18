# money/reports/urls.py
from django.conf import settings
from django.conf.urls import patterns, include, url


urlpatterns = patterns('',

    url(r'^bymonth/$', 'money.reports.views.by_month_view', name="money_report_by_month"),
    url(r'^bymonth/(?P<currency>\w[\w/-]*)$', 'money.reports.views.by_month_view', name="money_report_by_month"),
    
    url(r'^byyear/$', 'money.reports.views.by_year_view', name="money_report_by_year"),
    url(r'^byyear/(?P<currency>\w[\w/-]*)$', 'money.reports.views.by_year_view', name="money_report_by_year"),
    
)
