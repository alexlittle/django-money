import calendar
from django.conf import settings
from datetime import datetime
from dateutil.relativedelta import relativedelta

def base_currency(request):
    return {'BASE_CURRENCY': settings.BASE_CURRENCY}

def kollektiivi_menu(request):
    start_date = datetime(2023, 6, 1) 
    end_date = datetime.today()
    menu = []
    no_months =  (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 3
    for i in range(0, no_months):
        report_month = start_date + relativedelta(months=i)
        menu.append(dict(month=report_month.month,
                         year=report_month.year,
                         name=calendar.month_name[report_month.month]))
    return {'KOLLEKTIIVI_MENU': menu}
