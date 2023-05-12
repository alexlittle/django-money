import datetime

from django.shortcuts import render

from money.models import Transaction


def monthly_transactions_view(request, year=0, month=0):

    if year == 0:
        year = datetime.datetime.today().year
        month = datetime.datetime.today().month

    transactions = Transaction.objects.filter(date__year=year, date__month=month).order_by("date")

    return render(request, 'money/reports/monthly_transactions.html',
                  {'transactions': transactions})
