import datetime
import dateutil.relativedelta

from django.conf import settings
from django.db.models import Sum, Max
from django.shortcuts import render
from django.template import RequestContext
from django.utils import timezone

from money.models import Account, Transaction, Valuation, RegularPayment, ExchangeRate


def by_month_view(request):
    
    tz = timezone.get_default_timezone()
    now = datetime.datetime.now()
    
    report = []
    
    for i in range(96,-1,-1):
        report_month = now - dateutil.relativedelta.relativedelta(months=i)
        
        report_row = {}
        report_row['month'] = report_month.month
        report_row['year'] = report_month.year
        report_row['sum_in'] = 0
        report_row['sum_out'] = 0
        for k,v in settings.CURRENCIES_AVAILABLE:
            transactions = Transaction.objects.filter(account__currency=k, date__month=report_month.month, date__year=report_month.year).exclude(payment_type='Transfer').\
                                                extra(select={'year': "EXTRACT(year FROM date)", 'month': "EXTRACT(month FROM date)"}).\
                                                values('year','month').\
                                                annotate(sum_in=Sum('credit'),sum_out=Sum('debit'))
            date = datetime.datetime(report_month.year, report_month.month, 1, tzinfo=tz)
            
            rate = ExchangeRate.at_date(date, settings.BASE_CURRENCY, k)
            for t in transactions:
                report_row['sum_in']  += t['sum_in']/rate
                report_row['sum_out']  += t['sum_out']/rate
        report_row['balance'] = report_row['sum_in'] - report_row['sum_out']
                
        report.append(report_row)
        
    report.reverse()
    return render(request,'money/reports/by_month.html',
                              {'report': report})
    
def by_year_view(request):
    
    tz = timezone.get_default_timezone()
    now = datetime.datetime.now()
    
    report = []
    
    for i in range(10,-1,-1):
        report_year = now - dateutil.relativedelta.relativedelta(years=i)
        
        report_row = {}
        report_row['year'] = report_year.year
        report_row['sum_in'] = 0
        report_row['sum_out'] = 0
        for k,v in settings.CURRENCIES_AVAILABLE:
            transactions = Transaction.objects.filter(account__currency=k, date__year=report_year.year).exclude(payment_type='Transfer').\
                                                extra(select={'year': "EXTRACT(year FROM date)"}).\
                                                values('year').\
                                                annotate(sum_in=Sum('credit'),sum_out=Sum('debit'))
            date = datetime.datetime(report_year.year, 12, 31, tzinfo=tz)
            
            rate = ExchangeRate.at_date(date, settings.BASE_CURRENCY, k)
            for t in transactions:
                report_row['sum_in']  += t['sum_in']/rate
                report_row['sum_out']  += t['sum_out']/rate
        report_row['balance'] = report_row['sum_in'] - report_row['sum_out']
                
        report.append(report_row)
        
    report.reverse()
    return render(request,'money/reports/by_year.html',
                               {'report': report})
    
    
def graph_view(request):
    
    now = datetime.datetime.now()
    tz = timezone.get_default_timezone()
    
    balances = []

    for i in range(96,-1,-1):
        balance = {} 
        old_date = now - dateutil.relativedelta.relativedelta(months=i)
        last_day = datetime.datetime(int(old_date.strftime("%Y")), int(old_date.strftime("%m")), 1, 23, 59, tzinfo=tz)\
                     + dateutil.relativedelta.relativedelta(day=1, months=+1, days=-1)
        
        cash_total = 0
        accs = Account.objects.filter(type='cash') 
        for acc in accs:
            if Account.get_balance_base_currency_at_date(acc,last_day):
                cash_total += Account.get_balance_base_currency_at_date(acc,last_day)
        
        invest_total = 0 
        accs = Account.objects.filter(type='invest') 
        for acc in accs:
            if Account.get_valuation_base_currency_at_date(acc,last_day):
                invest_total += Account.get_valuation_base_currency_at_date(acc,last_day)
                                            
        balance['date'] = last_day
        balance['total'] = cash_total + invest_total
        balance['cash'] = cash_total
        balance['invest'] = invest_total
        
        balances.append(balance) 
                            
    
    return render(request,'money/reports/graph.html',
                              {'balances': balances})
    