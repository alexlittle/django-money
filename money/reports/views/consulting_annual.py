
from django.db.models import Sum
from django.shortcuts import render

from money.models import Transaction


def consulting_annual(request, year):
    CONSULTING_ID = 47
    CONSULTING_EXTRAS_ID = 49

    # get income
    income = Transaction.objects \
        .filter(account_id=CONSULTING_ID, date__year=year) \
        .exclude(payment_type='Transfer') \
        .aggregate(total=Sum('credit'))

    print(income)

    # get expenses (core)
    core_expenses = Transaction.objects \
        .filter(account_id=CONSULTING_ID, date__year=year) \
        .exclude(payment_type='Transfer') \
        .aggregate(total=Sum('debit'))

    print(core_expenses)

    # get expenses (extras)
    extra_expenses = Transaction.objects \
        .filter(account_id=CONSULTING_EXTRAS_ID, date__year=year) \
        .exclude(payment_type='Transfer') \
        .aggregate(total=Sum('debit'))

    print(extra_expenses)

    # total

    return render(request, 'money/reports/consulting_annual.html',
                  {'year': year,
                   'income': income['total'],
                   'core_expenses': core_expenses['total'],
                   'extra_expenses': extra_expenses['total']})
