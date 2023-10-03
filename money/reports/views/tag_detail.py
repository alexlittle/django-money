
from django.db.models import Sum, F
from django.views.generic import TemplateView

from money.models import Tag, Transaction


class TagDetailView(TemplateView):

    template_name = 'money/reports/tag_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tag_id = kwargs['tag_id']
        context['tag'] = Tag.objects.get(pk=tag_id)
        context['totals_by_year'] = Tag.objects.filter(pk=tag_id) \
            .values('name', year=F('transactiontag__transaction__date__year')) \
            .annotate(sum_in=Sum('transactiontag__transaction__credit'), sum_out=Sum('transactiontag__transaction__debit'))
        context['transactions'] = Transaction.objects.filter(transactiontag__tag__pk=tag_id).order_by("-date")
        return context
