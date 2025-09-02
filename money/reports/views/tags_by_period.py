import datetime

from django.db.models import Sum, F
from django.utils import timezone
from django.views.generic import TemplateView

from money.models import Tag, AccountingPeriod, Transaction, TransactionTag


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
                                                  start_date__lte=timezone.now()).order_by('-start_date')

        context['year'] = year
        context['years'] = years
        context['periods'] = periods

        categories = Tag.objects.filter(transactiontag__transaction__date__year=year).values_list('category', flat=True)
        categories = set(categories)

        print(categories)
        context['categories'] = []

        for category in categories:
            category_year = {
                'category': category,
                'sum_in': 0,
                'sum_out': 0
            }
            transaction_tags = TransactionTag.objects.filter(tag__category=category, transaction__date__year=year)
            for transaction_tag in transaction_tags:
                category_year['sum_in'] += transaction_tag.get_credit_in_base_currency()
                category_year['sum_out'] += transaction_tag.get_debit_in_base_currency()
            context['categories'].append(category_year)

        context['tags'] = []
        tags = Tag.objects.filter(transactiontag__transaction__date__year=year).distinct()

        print(tags)
        for tag in tags:
            tag_year = {
                'tag': tag,
                'sum_in': 0,
                'sum_out': 0
            }
            print(tag_year)
            transaction_tags = TransactionTag.objects.filter(tag__id=tag.id, transaction__date__year=year)
            for transaction_tag in transaction_tags:
                tag_year['sum_in'] += transaction_tag.get_credit_in_base_currency()
                tag_year['sum_out'] += transaction_tag.get_debit_in_base_currency()
            context['tags'].append(tag_year)

        #context['tags'] = Tag.objects.filter(transactiontag__transaction__date__year=year) \
        #    .values('id', 'name', 'category', year=F('transactiontag__transaction__date__year')) \
        #   .annotate(sum_in=Sum('transactiontag__allocation_credit'), sum_out=Sum('transactiontag__allocation_debit'))



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
                                                  start_date__lte=timezone.now()).order_by('-start_date')
        context['period'] = period
        context['years'] = years
        context['periods'] = periods
        context['tags'] = Tag.objects.filter(transactiontag__transaction__date__gte=period.start_date,
                                             transactiontag__transaction__date__lte=period.end_date) \
            .values('id', 'name', 'category') \
            .annotate(sum_in=Sum('transactiontag__allocation_credit'), sum_out=Sum('transactiontag__allocation_debit'))
        context['categories'] = Tag.objects.filter(transactiontag__transaction__date__gte=period.start_date,
                                                    transactiontag__transaction__date__lte=period.end_date) \
            .values('category') \
            .annotate(sum_in=Sum('transactiontag__allocation_credit'), sum_out=Sum('transactiontag__allocation_debit'))
        return context
