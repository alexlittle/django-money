
from django.db.models import Sum, F
from django.views.generic import TemplateView

from money.models import Tag, TransactionTag, AccountingPeriod


class TagDetailView(TemplateView):

    template_name = 'money/reports/tag_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tag_id = kwargs['tag_id']
        period_id = kwargs.get('period_id')

        context['tag'] = Tag.objects.get(pk=tag_id)
        context['totals_by_year'] = Tag.objects.filter(pk=tag_id) \
            .values('name', year=F('transactiontag__transaction__date__year')) \
            .annotate(sum_in=Sum('transactiontag__allocation_credit'), sum_out=Sum('transactiontag__allocation_debit'))
        transaction_tags = TransactionTag.objects.filter(tag__pk=tag_id)
        if period_id:
            accounting_period = AccountingPeriod.objects.get(pk=period_id)
            context['period'] = accounting_period
            context['transactiontags'] = transaction_tags.filter(transaction__date__gte=accounting_period.start_date,
                                                                transaction__date__lte=accounting_period.end_date,).order_by('-transaction__date')
        else:
            context['transactiontags'] = transaction_tags.order_by('-transaction__date')
        return context
