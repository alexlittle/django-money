import datetime
import dateutil.relativedelta

from django.conf import settings
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from money.models import Transaction, ExchangeRate


def tags_by_year_view(request):

    tz = timezone.get_default_timezone()
    now = datetime.datetime.now()

    report = []

    for i in range(10, -1, -1):