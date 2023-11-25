
from django.db.models import Sum
from django.shortcuts import render

from money.models import Transaction


def consulting_annual(request, year):
    CONSULTING_ID = 47
    CONSULTING_EXTRAS_ID = 49

    transactions = Transaction.objects \
        .filter(account_id__in=(CONSULTING_ID, CONSULTING_EXTRAS_ID), date__year=year) \
        .exclude(payment_type='Transfer') \
        .exclude(transactiontag__tag__name="kollektiivi") \

    print(transactions)
    # all transactions
    # excluding kollektiivi
    tax = transactions.filter(description__startswith="Tax") \
        .aggregate(total_credit=Sum('credit'), total_debit=Sum('debit'))
    varma = transactions.filter(description__startswith="Varma") \
        .aggregate(total_credit=Sum('credit'), total_debit=Sum('debit'))

    # totals
    totals = transactions.exclude(description__startswith="Tax") \
                        .exclude(description__startswith="Varma") \
                        .aggregate(total_credit=Sum('credit'), total_debit=Sum('debit'))

    transactions = transactions.order_by("date")
    return render(request, 'money/reports/consulting_annual.html',
                  {'year': year,
                   'transactions': transactions,
                   'totals': totals,
                   'tax': tax,
                   'varma': varma })
