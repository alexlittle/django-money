
from django.urls import include, path

from money import views as money_views

app_name = 'money'

urlpatterns = [
    path('', money_views.home_view, name="money_home"),
    path('account/<int:account_id>/', money_views.account_view, name="money_account"),
    path('reports/', include('money.reports.urls')),
    path('transaction/<int:transaction_id>/toggle/', money_views.transaction_toggle, name="transaction_toggle"),
    path('transaction/<int:transaction_id>/receipt/', money_views.transaction_receipt_view, name="transaction_receipt"),
]
