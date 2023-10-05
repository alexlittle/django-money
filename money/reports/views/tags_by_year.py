import datetime

from django.db.models import Sum, F
from django.views.generic import TemplateView

from money.models import Tag, Transaction


class TagsByYearView(TemplateView):

    template_name = 'money/reports/tags_by_year.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            year = kwargs['year']
        except KeyError:
            year = datetime.datetime.today().year

        context['year'] = year
        context['tags'] = Tag.objects.filter(transactiontag__transaction__date__year=year) \
            .values('id', 'name', 'category', year=F('transactiontag__transaction__date__year')) \
            .annotate(sum_in=Sum('transactiontag__transaction__credit'), sum_out=Sum('transactiontag__transaction__debit'))
        return context
