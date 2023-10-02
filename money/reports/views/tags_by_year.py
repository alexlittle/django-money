
from django.db.models import Sum
from django.views.generic import TemplateView

from money.models import Tag, Transaction, ExchangeRate


class TagsByYearView(TemplateView):
    
    template_name = 'money/reports/tags_by_year.html'
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = kwargs['year']
        context['year'] = year
        context['tags'] = Tag.objects.filter(transactiontag__transaction__date__year=year) \
            .extra(select={'year': "EXTRACT(year FROM date)"}) \
            .values('name', 'year') \
            .annotate(sum_in=Sum('transactiontag__transaction__credit'), sum_out=Sum('transactiontag__transaction__debit'))
        print(context['tags'])
        return context
    
    def get_queryset(self, year):
        data = Tag.objects.filter(transactiontag__transaction__date__year=year).extra(select={'year': "EXTRACT(year FROM date)"}).values('name', 'year')
        return data