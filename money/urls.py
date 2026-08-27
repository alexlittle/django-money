from django.urls import include, path

from money import views as money_views

app_name = "money"

urlpatterns = [
    path("", money_views.HomeView.as_view(), name="home"),
    path("account/<int:account_id>/", money_views.AccountView.as_view(), name="money_account"),
    path("reports/", include("money.reports.urls")),
    path(
        "transaction/<int:transaction_id>/toggle/",
        money_views.TransactionToggleView.as_view(),
        name="transaction_toggle",
    ),
]
