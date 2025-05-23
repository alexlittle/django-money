
from django.urls import path

from money.reports import views as report_views


urlpatterns = [
    path('graph/', report_views.SummaryGraph.as_view(), name="graph"),
    path('graph/annual/<int:year>/', report_views.AnnualGraphsView.as_view(), name="graphs_annual"),
    path('investment-graph/', report_views.graph_investment_view, name="investment_graph"),
    path('bymonth/', report_views.by_month_view, name="by_month"),
    path('monthly-transactions/', report_views.monthly_transactions_view, name="monthly_transactions"),
    path('monthly-transactions/<int:year>/<int:month>/', report_views.monthly_transactions_view, name="monthly_transactions"),
    path('byyear/', report_views.by_year_view, name="by_year"),
    path('consulting/<int:period_id>/', report_views.consulting_quarters, name="consulting"),
    path('annual/<int:year>/', report_views.consulting_annual, name="consulting_annual"),
    path('bills/', report_views.bills_view, name="bills"),
    path('kollektiivi/<int:year>/<int:month>/', report_views.kollektiivi_monthly, name="kollektiivi_monthly"),

    path('tags/', report_views.TagsByYearView.as_view(), name="tags_all"),
    path('tags/year/<int:year>/', report_views.TagsByYearView.as_view(), name="tags_by_year"),
    path('tags/period/<int:period_id>/', report_views.TagsByPeriodView.as_view(), name="tags_by_period"),
    path('tag/<int:tag_id>/', report_views.TagDetailView.as_view(), name="tag_detail"),
    path('tag/<int:tag_id>/<int:period_id>/', report_views.TagDetailView.as_view(), name="tag_detail"),
    path('tags/category/<str:category>/', report_views.TagsByCategoryView.as_view(), name="tags_by_category"),
    path('tags/category/<str:category>/<int:period_id>/', report_views.TagsByCategoryView.as_view(), name="tags_by_category"),

    path('budget/', report_views.BudgetView.as_view(), name="budget_all"),
    path('budget/<int:period_id>/', report_views.BudgetByPeriodView.as_view(), name="budget_by_period"),

    path('invoices/<int:year>/<int:month>/', report_views.MonthlyInvoicesView.as_view(), name="monthly_invoices"),
]
