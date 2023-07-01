import calendar

from datetime import datetime, timedelta

from django.db.models import Sum, F
from django.shortcuts import render

from money.models import Account, Transaction

CONSULTING_ID = 47
KOLLEKTIIVI_TAG = "kollektiivi"
KOLLEKTIIVI_EXTRAS_ID = 53
    
def kollektiivi_balance_at_date(date):
    trans_cred = Transaction.objects.filter(
        account_id__in=(CONSULTING_ID, KOLLEKTIIVI_EXTRAS_ID),
        date__lte=date,
        transactiontag__tag__name=KOLLEKTIIVI_TAG).annotate(
            credit_percent=F("credit")*F("transactiontag__percent")/100
            ).aggregate(credit_sum=Sum("credit_percent"))
    trans_deb = Transaction.objects.filter(
        account_id__in=(CONSULTING_ID, KOLLEKTIIVI_EXTRAS_ID),
        date__lte=date,
        transactiontag__tag__name=KOLLEKTIIVI_TAG).annotate(
            debit_percent=F("debit")*F("transactiontag__percent")/100
            ).aggregate(debit_sum=Sum("debit_percent"))

    if trans_deb['debit_sum'] is None and trans_cred['credit_sum'] is None:
        return 0
    elif trans_deb['debit_sum'] is None:
        return trans_cred['credit_sum']
    elif trans_cred['credit_sum'] is None:
        return trans_deb['debit_sum']
    else:
        return trans_cred['credit_sum'] - trans_deb['debit_sum']

def kollektiivi_monthly(request, year, month):

    consulting = Transaction.objects.filter(
        account_id__in=(CONSULTING_ID, KOLLEKTIIVI_EXTRAS_ID),
        date__month=month,
        date__year=year,
        transactiontag__tag__name=KOLLEKTIIVI_TAG).annotate(
            debit_percent=F("debit")*F("transactiontag__percent")/100,
            credit_percent=F("credit")*F("transactiontag__percent")/100,
            sales_tax_charged_percent=F("sales_tax_charged")*F("transactiontag__percent")/100,
            sales_tax_paid_percent=F("sales_tax_paid")*F("transactiontag__percent")/100,
            ).order_by('date')

    data = []
    
    for c in consulting:
        obj = {'transaction': c,
               'balance': kollektiivi_balance_at_date(c.date)}
        data.append(obj)

    start_date = datetime(year, month, 1, 0, 0, 0) - timedelta(days=1)
    end_date = datetime(year, month, calendar.monthrange(year, month)[1], 23, 59, 59)
    
    opening_balance = kollektiivi_balance_at_date(start_date)
    closing_balance = kollektiivi_balance_at_date(end_date)

    totals = consulting.aggregate(total_credit=Sum("credit_percent"),
                                  total_debit=Sum("debit_percent"),
                                  total_alv_charged=Sum('sales_tax_charged_percent'),
                                  total_alv_paid=Sum('sales_tax_paid_percent'))
        
        
    return render(request, 'money/reports/kollektiivi.html',
                  {'data': data,
                   'opening_balance': opening_balance,
                   'closing_balance': closing_balance,
                   'start_date': datetime(year, month, 1),
                   'end_date': end_date,
                   'totals': totals})
    