
from django.conf.urls import url

from money.reports import views as report_views

app_name = 'reports'

urlpatterns = [
    url(r'^graph/$', report_views.graph_view, name="graph"),
    url(r'^bymonth/$',
        report_views.by_month_view,
        name="by_month"),
    url(r'^byyear/$', report_views.by_year_view, name="by_year"),
    url(r'^consulting/(?P<quarter>\w[\w/-]*)/$',
        report_views.consulting_quarters, name="consulting"),
    url(r'^annual/(?P<year>\d+)/$',
        report_views.consulting_annual, name="consulting_annual"),
    url(r'^bills/$',
        report_views.bills_view, name="bills"),
]
