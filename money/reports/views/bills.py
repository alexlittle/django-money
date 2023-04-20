
from django.db.models import Sum, Count, F
from django.db.models.functions import ExtractYear
from django.shortcuts import render

from money.models import Transaction


def bill_transaction_filter(description_filtered):
    return description_filtered \
                .annotate(year=ExtractYear('date')) \
                .values('year') \
                .filter(year__gte=2016) \
                .annotate(total=Sum('debit'), no_payments=Count('id')) \
                .annotate(payment_avg=F('total') / F('no_payments'),
                          monthly_avg=F('total')/12) \
                .order_by('-year')


def bills_view(request):

    electric = bill_transaction_filter(Transaction.objects.filter(description="Fortum - electric"))
    rubbish = bill_transaction_filter(Transaction.objects.filter(description__icontains="rubbish"))
    water = bill_transaction_filter(Transaction.objects.filter(description__icontains="water bill"))
    house_tax = bill_transaction_filter(Transaction.objects.filter(description__icontains="house tax"))
    car = bill_transaction_filter(Transaction.objects.filter(description__istartswith="car "))
    insurance = bill_transaction_filter(Transaction.objects.filter(description__icontains="insurance"))
    phone = bill_transaction_filter(Transaction.objects.filter(description__icontains="elisa", account__id=39))
    accounting_fees = bill_transaction_filter(Transaction.objects.filter(description__icontains="accounting"))

    return render(request, 'money/reports/bills.html',
                  {'electric': electric,
                   'rubbish': rubbish,
                   'water': water,
                   'house_tax': house_tax,
                   'car': car,
                   'insurance': insurance,
                   'phone': phone,
                   'accounting_fees': accounting_fees})
