
from django.db.models import Sum, F
from django.utils import timezone

from django.views.generic import TemplateView

from money.models import Tag, AccountingPeriod, Transaction


class TagsByCategoryView(TemplateView):

    template_name = 'money/reports/tags_by_category.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = kwargs['category']
        tags = Tag.objects.filter(category=category)
        context['category'] = category

        context['totals_by_year'] = Transaction.objects.filter(transactiontag__tag__in=tags) \
            .values(year=F('date__year')).distinct() \
            .annotate(sum_in=Sum('credit'),
                      sum_out=Sum('debit'),
                      balance=Sum('credit')-Sum('debit'))

        aps = AccountingPeriod.objects.filter(active=True,
                                              start_date__lte=timezone.now()).order_by('-start_date')
        periods = []
        for ap in aps:
            temp = Transaction.objects.filter(transactiontag__tag__in=tags,
                               date__gte=ap.start_date,
                               date__lte=ap.end_date) \
                .values(category=F('transactiontag__tag__category')).distinct()  \
                .annotate(sum_in=Sum('credit'),
                          sum_out=Sum('debit')).order_by('category').first()
            p = {
                'title': ap.title,
                'sum_in': temp['sum_in'],
                'sum_out': temp['sum_out'],
                'balance': temp['sum_in'] - temp['sum_out']
            }
            periods.append(p)

        context['periods'] = periods

        context['transactions'] = Transaction.objects.filter(transactiontag__tag__in=tags).distinct() .order_by("-date")
        return context
