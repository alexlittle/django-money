from datetime import datetime

from django.conf import settings
from django.utils import timezone

from money.models import AccountingPeriod, Tag


def base_currency(request):
    return {"BASE_CURRENCY": settings.BASE_CURRENCY}


def get_accounting_periods(request):
    datetime.today()
    aps = AccountingPeriod.objects.filter(active=True, start_date__lte=timezone.now()).order_by(
        "-start_date"
    )
    return {"ACCOUNTING_PERIODS": aps}


def tags_menu(request):
    menu = []
    tags = Tag.objects.order_by().values("category").distinct()
    for t in tags:
        menu.append(t)
    return {"TAG_MENU": menu}
