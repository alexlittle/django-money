
import datetime
import os

from django.conf import settings
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views.generic.edit import FormView

from wkhtmltopdf.views import PDFTemplateResponse

from money.models import Account, Transaction, RegularPayment
from money.forms import InvoicesForm

def home_view(request):
    update_regular_payments()

    cash_accounts = []
    for k, v in settings.CURRENCIES_AVAILABLE:
        currency = {}
        currency['currency'] = k
        currency['account'] = Account.objects.filter(active=True, type='cash', currency=k)
        currency['total_balance'] = Account.get_balance_total('cash', k)
        currency['total_on_statement'] = Account.get_on_statment_total('cash', k)
        currency['total_base_currency'] = Account.get_balance_base_currency_total('cash', k)
        cash_accounts.append(currency)

    invest_accounts = []
    for k, v in settings.CURRENCIES_AVAILABLE:
        currency = {}
        currency['currency'] = k
        currency['account'] = Account.objects.filter(active=True, type='invest', currency=k)
        currency['total_valuation'] = Account.get_valuation_total('invest', k)
        currency['total_base_currency'] = Account.get_valuation_base_currency_total('invest', k)
        invest_accounts.append(currency)

    property = {}
    property['accounts'] = Account.objects.filter(active=True, type='property')
    property['total_base_currency'] = Account.get_val_base_currency_total('property')

    pensions = {}
    pensions['accounts'] = Account.objects.filter(active=True, type='pension')
    pensions['total_base_currency'] = Account.get_val_base_currency_total('pension')
    pensions['total_est_monthly'] = Account.get_monthly_val_base_currency_total('pension')

    return render(request, 'money/home.html',
                  {'cash_accounts': cash_accounts,
                   'invest_accounts': invest_accounts,
                   'property': property,
                   'pensions': pensions})


def account_view(request, account_id):
    account = Account.objects.get(pk=account_id)
    trans = Transaction.objects.filter(account=account).order_by('-date')

    paginator = Paginator(trans, 100)

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        transactions = paginator.page(page)
    except (EmptyPage, InvalidPage):
        transactions = paginator.page(paginator.num_pages)

    return render(request, 'money/account.html',
                  {'account': account,
                   'page': transactions})


def transaction_toggle(request, transaction_id):
    transaction = Transaction.objects.get(pk=transaction_id)
    if transaction.on_statement:
        transaction.on_statement = False
    else:
        transaction.on_statement = True
    transaction.save()
    return HttpResponseRedirect(reverse('money:money_account',
                                        kwargs={'account_id':
                                                transaction.account.id}))


def update_regular_payments():
    payments = RegularPayment.objects.filter(next_date__lte=timezone.now())
    for rp in payments:
        # add to transactions
        transaction = Transaction(account=rp.account,
                                  payment_type=rp.payment_type,
                                  credit=rp.credit,
                                  debit=rp.debit,
                                  description=rp.description)
        transaction.save()
        # update regular payment
        next_date = rp.next_date + datetime.timedelta(days=31)
        rp.next_date = next_date
        rp.save()


def transaction_receipt_view(request, transaction_id):
    transaction = Transaction.objects.get(pk=transaction_id)
    return render(request, 'money/receipt.html',
                  {'transaction': transaction})


def transaction_receipt_view(request, transaction_id):
    transaction = Transaction.objects.get(pk=transaction_id)
    template = 'money/receipt.html'

    context = {
        'transaction': transaction,
    }
    return PDFTemplateResponse(request=request,
                               show_content_in_browser=False,
                               filename="%s-receipt-%d.pdf" % (transaction.date.strftime("%Y-%m-%d"), transaction_id),
                               template=template,
                               context=context)


class CreateInvoicesView(FormView):

    template_name = 'money/create_invoices.html'
    form_class = InvoicesForm
    success_url = "/invoices/create/done/"

    def form_valid(self, form):
        invoice_date = form.cleaned_data['issue_date']
        due_date = form.cleaned_data['due_date']
        title = form.cleaned_data['title']
        send_to_ids = form.cleaned_data['send_to']
        ref_nos = form.cleaned_data['ref_nos'].split(',')
        template = 'money/kollektiivi_invoice.html'

        tempdate = datetime.datetime.strptime(due_date, "%d.%m.%Y").date()
        year = tempdate.year
        month = '{:02d}'.format(tempdate.month)
        for idx, invoice in enumerate(send_to_ids):

            context = {
                'invoice_date': invoice_date,
                'due_date': due_date,
                'title': title,
                'ref': ref_nos[idx],
                'invoice_info': invoice,
                'acc_name': settings.INVOICE_ACCOUNT_NAME,
                'acc_iban': settings.INVOICE_ACCOUNT_IBAN,
                'acc_bic': settings.INVOICE_ACCOUNT_BIC
            }
            response = PDFTemplateResponse(request=self.request,
                                           filename="invoice.pdf",
                                           template=template,
                                           context=context)

            filename = "invoice-{year}-{month}-{name}-{ref}.pdf".format(year=year,
                                                                        month=month,
                                                                        name=invoice.name.lower(),
                                                                        ref=ref_nos[idx])
            output_path = os.path.join(settings.INVOICE_OUTPUT_DIR, filename)
            with open(output_path, "wb") as f:
                f.write(response.rendered_content)

            #return render(self.request, template, context)
        return super().form_valid(form)