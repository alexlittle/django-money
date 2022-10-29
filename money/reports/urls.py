
from django.urls import path

from money.reports import views as report_views

app_name = 'reports'

urlpatterns = [
    path('graph/', report_views.graph_view, name="graph"),
    path('bymonth/', report_views.by_month_view, name="by_month"),
    path('byyear/', report_views.by_year_view, name="by_year"),
    path('consulting/<str:quarter>/',
        report_views.consulting_quarters, name="consulting"),
    path('annual/<int:year>/',
        report_views.consulting_annual, name="consulting_annual"),
    path('bills/',
        report_views.bills_view, name="bills"),
]
