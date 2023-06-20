import calendar

from datetime import datetime, timedelta

from django.db.models import Sum
from django.shortcuts import render

from money.models import Account, Transaction


def kollektiivi_monthly(request, year, month):
    CONSULTING_ID = 47
    KOLLEKTIIVI_TAG = "kollektiivi"

    consulting_account = Account.objects.get(pk=CONSULTING_ID)
    consulting = Transaction.objects.filter(
        account_id=CONSULTING_ID,
        date__month=month,
        date__year=year,
        transactiontag__tag__name=KOLLEKTIIVI_TAG).order_by('date')

    data = []
    for c in consulting:
        obj = {'transaction': c,
               'balance': Account.get_balance_base_currency_at_date(c.account, c.date, tag=KOLLEKTIIVI_TAG)}
        if c.debit != 0 and c.sales_tax_paid != 0:
            obj['ex_sales_tax'] = c.debit - c.sales_tax_paid
        data.append(obj)

    start_date = datetime(year, month, 1) - timedelta(days=1)
    end_date = datetime(year, month, calendar.monthrange(year, month)[1])
    
    opening_balance = Account.get_balance_base_currency_at_date(consulting_account, start_date, tag=KOLLEKTIIVI_TAG)
    closing_balance = Account.get_balance_base_currency_at_date(consulting_account, end_date, tag=KOLLEKTIIVI_TAG)

    totals = consulting.aggregate(total_credit=Sum("credit"),
                                  total_debit=Sum("debit"),
                                  total_alv_charged=Sum('sales_tax_charged'),
                                  total_alv_paid=Sum('sales_tax_paid'))
        
        
    return render(request, 'money/reports/kollektiivi.html',
                  {'data': data,
                   'opening_balance': opening_balance,
                   'closing_balance': closing_balance,
                   'start_date': datetime(year, month, 1),
                   'end_date': end_date,
                   'totals': totals})
    