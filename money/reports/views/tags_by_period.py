import datetime

from django.db.models import Sum, F
from django.views.generic import TemplateView

from money.models import Tag, AccountingPeriod


class TagsByYearView(TemplateView):

    template_name = 'money/reports/tags_by_period.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            year = kwargs['year']
        except KeyError:
            year = datetime.datetime.today().year

        years = []
        for i in range(2022, datetime.datetime.today().year+1, 1):
            years.append(i)

        periods = AccountingPeriod.objects.filter(active=True,
                                                  start_date__lte=datetime.datetime.today()).order_by('-start_date')

        context['year'] = year
        context['years'] = years
        context['periods'] = periods
        context['tags'] = Tag.objects.filter(transactiontag__transaction__date__year=year) \
            .values('id', 'name', 'category', year=F('transactiontag__transaction__date__year')) \
            .annotate(sum_in=Sum('transactiontag__transaction__credit'), sum_out=Sum('transactiontag__transaction__debit'))
        context['categories'] = Tag.objects.filter(transactiontag__transaction__date__year=year) \
            .values('category', year=F('transactiontag__transaction__date__year')) \
            .annotate(sum_in=Sum('transactiontag__transaction__credit'), sum_out=Sum('transactiontag__transaction__debit'))
        return context

class TagsByPeriodView(TemplateView):

    template_name = 'money/reports/tags_by_period.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        period_id = kwargs['period_id']

        period = AccountingPeriod.objects.get(pk=period_id)

        years = []
        for i in range(2022, datetime.datetime.today().year+1, 1):
            years.append(i)

        periods = AccountingPeriod.objects.filter(active=True,
                                                  start_date__lte=datetime.datetime.today()).order_by('-start_date')
        context['period'] = period
        context['years'] = years
        context['periods'] = periods
        context['tags'] = Tag.objects.filter(transactiontag__transaction__date__gte=period.start_date,
                                             transactiontag__transaction__date__lte=period.end_date) \
            .values('id', 'name', 'category') \
            .annotate(sum_in=Sum('transactiontag__transaction__credit'), sum_out=Sum('transactiontag__transaction__debit'))
        context['categories'] = Tag.objects.filter(transactiontag__transaction__date__gte=period.start_date,
                                                    transactiontag__transaction__date__lte=period.end_date) \
            .values('category') \
            .annotate(sum_in=Sum('transactiontag__transaction__credit'), sum_out=Sum('transactiontag__transaction__debit'))
        return context
