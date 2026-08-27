import datetime

from django.conf import settings
from django.core.paginator import EmptyPage, InvalidPage, Paginator
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView, View

from money.models import Account, RegularPayment, Transaction


class HomeView(TemplateView):
    template_name = "money/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        update_regular_payments()

        cash_accounts = []
        for k, _v in settings.CURRENCIES_AVAILABLE:
            currency = {}
            currency["currency"] = k
            currency["account"] = Account.objects.filter(active=True, type="cash", currency=k)
            currency["total_balance"] = Account.get_balance_total("cash", k)
            currency["total_on_statement"] = Account.get_on_statment_total("cash", k)
            currency["total_base_currency"] = Account.get_balance_base_currency_total("cash", k)
            cash_accounts.append(currency)

        invest_accounts = []
        for k, _v in settings.CURRENCIES_AVAILABLE:
            currency = {}
            currency["currency"] = k
            currency["account"] = Account.objects.filter(active=True, type="invest", currency=k)
            currency["total_valuation"] = Account.get_valuation_total("invest", k)
            currency["total_base_currency"] = Account.get_valuation_base_currency_total("invest", k)
            invest_accounts.append(currency)

        property = {}
        property["accounts"] = Account.objects.filter(active=True, type="property")
        property["total_base_currency"] = Account.get_val_base_currency_total("property")

        pensions = {}
        pensions["accounts"] = Account.objects.filter(active=True, type="pension")
        pensions["total_base_currency"] = Account.get_val_base_currency_total("pension")
        pensions["total_est_monthly"] = Account.get_monthly_val_base_currency_total("pension")

        context["cash_accounts"] = cash_accounts
        context["invest_accounts"] = invest_accounts
        context["property"] = property
        context["pensions"] = pensions
        return context


class AccountView(TemplateView):
    template_name = "money/account.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = Account.objects.get(pk=kwargs["account_id"])
        trans = Transaction.objects.filter(account=account).order_by("-date")

        paginator = Paginator(trans, 100)

        try:
            page = int(self.request.GET.get("page", "1"))
        except ValueError:
            page = 1

        try:
            transactions = paginator.page(page)
        except (EmptyPage, InvalidPage):
            transactions = paginator.page(paginator.num_pages)

        context["account"] = account
        context["page"] = transactions
        return context


class TransactionToggleView(View):
    def get(self, request, transaction_id):
        transaction = Transaction.objects.get(pk=transaction_id)
        if transaction.on_statement:
            transaction.on_statement = False
        else:
            transaction.on_statement = True
        transaction.save()
        return HttpResponseRedirect(
            reverse("money:money_account", kwargs={"account_id": transaction.account.id})
        )


def update_regular_payments():
    payments = RegularPayment.objects.filter(next_date__lte=timezone.now())
    for rp in payments:
        # add to transactions
        transaction = Transaction(
            account=rp.account,
            payment_type=rp.payment_type,
            credit=rp.credit,
            debit=rp.debit,
            description=rp.description,
        )
        transaction.save()
        # update regular payment
        next_date = rp.next_date + datetime.timedelta(days=31)
        rp.next_date = next_date
        rp.save()
