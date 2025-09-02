
from django.db.models import Sum, F
from django.utils import timezone

from django.views.generic import TemplateView

from money.models import Tag, AccountingPeriod, Transaction


class TagsByCategoryView(TemplateView):

    template_name = 'money/reports/tags_by_category.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = kwargs['category']
        period_id = kwargs.get('period_id')

        tags = Tag.objects.filter(category=category)
        context['category'] = category

        context['totals_by_year'] = []

        years = Transaction.objects.filter(transactiontag__tag__in=tags).values_list('date__year', flat=True)
        years = set(years)

        for year in years:
            year_totals = {
                'year': year,
                'sum_in': 0,
                'sum_out': 0,
                'balance': 0
            }
            transactions = Transaction.objects.filter(transactiontag__tag__in=tags, date__year=year)
            for transaction in transactions:
                year_totals['sum_in'] += transaction.get_credit_in_base_currency()
                year_totals['sum_out'] += transaction.get_debit_in_base_currency()

            year_totals['balance'] = year_totals['sum_in'] - year_totals['sum_out']
            context['totals_by_year'].append(year_totals)

        context['periods'] = []
        aps = AccountingPeriod.objects.filter(active=True,
                                              start_date__lte=timezone.now()).order_by('-start_date')

        for ap in aps:
            p = {
                'id': ap.id,
                'title': ap.title,
                'sum_in': 0,
                'sum_out': 0,
                'balance': 0
            }
            transactions = Transaction.objects.filter(transactiontag__tag__in=tags,
                               date__gte=ap.start_date,
                               date__lte=ap.end_date)
            for transaction in transactions:
                p['sum_in'] += transaction.get_credit_in_base_currency()
                p['sum_out'] += transaction.get_debit_in_base_currency()
            p['balance'] = p['sum_in'] - p['sum_out']
            context['periods'].append(p)


        transactions = Transaction.objects.filter(transactiontag__tag__in=tags)
        if period_id:
            accounting_period = AccountingPeriod.objects.get(pk=period_id)
            context['period'] = accounting_period
            context['transactions'] = transactions.filter(date__gte=accounting_period.start_date,
                                                            date__lte=accounting_period.end_date).distinct().order_by('-date')
        else:
            context['transactions'] = transactions.distinct().order_by("-date")

        return context
