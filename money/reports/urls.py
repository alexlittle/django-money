
from django.urls import path

from money.reports import views as report_views


urlpatterns = [
    path('graph/', report_views.graph_view, name="graph"),
    path('investment-graph/', report_views.graph_investment_view, name="investment_graph"),
    path('bymonth/', report_views.by_month_view, name="by_month"),
    path('monthly-transactions/', report_views.monthly_transactions_view, name="monthly_transactions"),
    path('monthly-transactions/<int:year>/<int:month>/', report_views.monthly_transactions_view, name="monthly_transactions"),
    path('byyear/', report_views.by_year_view, name="by_year"),
    path('consulting/<str:quarter>/', report_views.consulting_quarters, name="consulting"),
    path('annual/<int:year>/', report_views.consulting_annual, name="consulting_annual"),
    path('bills/', report_views.bills_view, name="bills"),
]
