
from django.db.models import Sum, Count, F
from django.db.models.functions import ExtractYear
from django.shortcuts import render

from money.models import Transaction


def bills_view(request):

    electric = Transaction.objects.filter(
        description="Fortum - electric") \
        .annotate(year=ExtractYear('date')) \
        .values('year') \
        .filter(year__gte=2016) \
        .annotate(total=Sum('debit'), no_months=Count('id')) \
        .annotate(monthly_avg=F('total') / F('no_months')) \
        .order_by('-year')

    rubbish = Transaction.objects.filter(
        description__icontains="rubbish") \
        .annotate(year=ExtractYear('date')) \
        .values('year') \
        .filter(year__gte=2016) \
        .annotate(total=Sum('debit'), no_months=Count('id')) \
        .annotate(monthly_avg=F('total') / F('no_months')) \
        .order_by('-year')

    water = Transaction.objects.filter(
        description__icontains="water bill") \
        .annotate(year=ExtractYear('date')) \
        .values('year') \
        .filter(year__gte=2016) \
        .annotate(total=Sum('debit'), no_months=Count('id')) \
        .annotate(monthly_avg=F('total') / F('no_months')) \
        .order_by('-year')

    house_tax = Transaction.objects.filter(
        description__icontains="house tax") \
        .annotate(year=ExtractYear('date')) \
        .values('year') \
        .filter(year__gte=2016) \
        .annotate(total=Sum('debit'), no_months=Count('id')) \
        .annotate(monthly_avg=F('total') / F('no_months')) \
        .order_by('-year')

    car = Transaction.objects.filter(
        description__istartswith="car ") \
        .annotate(year=ExtractYear('date')) \
        .values('year') \
        .filter(year__gte=2016) \
        .annotate(total=Sum('debit'), no_months=Count('id')) \
        .annotate(monthly_avg=F('total') / F('no_months')) \
        .order_by('-year')

    insurance = Transaction.objects.filter(
        description__icontains="insurance") \
        .annotate(year=ExtractYear('date')) \
        .values('year') \
        .filter(year__gte=2016) \
        .annotate(total=Sum('debit'), no_months=Count('id')) \
        .annotate(monthly_avg=F('total') / F('no_months')) \
        .order_by('-year')
    
    phone = Transaction.objects.filter(
        description__icontains="elisa", account__id=39) \
        .annotate(year=ExtractYear('date')) \
        .values('year') \
        .filter(year__gte=2016) \
        .annotate(total=Sum('debit'), no_months=Count('id')) \
        .annotate(monthly_avg=F('total') / F('no_months')) \
        .order_by('-year')

    return render(request, 'money/reports/bills.html',
                  {'electric': electric,
                   'rubbish': rubbish,
                   'water': water,
                   'house_tax': house_tax,
                   'car': car,
                   'insurance': insurance,
                   'phone': phone})
