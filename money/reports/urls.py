
from django.conf.urls import url

from money.reports import views as report_views

urlpatterns = [
    url(r'^graph/$', report_views.graph_view, name="money_report_graph"),
    url(r'^bymonth/$',
        report_views.by_month_view,
        name="money_report_by_month"),
    url(r'^byyear/$', report_views.by_year_view, name="money_report_by_year"),
    url(r'^consulting/(?P<quarter>\w[\w/-]*)/$',
        report_views.consulting_quarters, name="money_consulting"),
    url(r'^annual/(?P<year>\d+)/$',
        report_views.consulting_annual, name="consulting_annual"),
]
