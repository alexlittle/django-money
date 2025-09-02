
from django.db.models import Sum, F
from django.views.generic import TemplateView

from money.models import Tag, Transaction, TransactionTag, AccountingPeriod


class TagDetailView(TemplateView):

    template_name = 'money/reports/tag_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tag_id = kwargs['tag_id']
        period_id = kwargs.get('period_id')

        context['tag'] = Tag.objects.get(pk=tag_id)
        transaction_tags = TransactionTag.objects.filter(tag__pk=tag_id)

        context['totals_by_year'] = []
        for year in transaction_tags.values(year=F('transaction__date__year')).distinct().order_by('-year'):
            trans_year = {
                'year': year['year'],
                'sum_in': 0,
                'sum_out': 0
            }
            for transaction_tag in transaction_tags.filter(transaction__date__year=year['year']):
                trans_year['sum_in'] += transaction_tag.get_credit_in_base_currency()
                trans_year['sum_out'] += transaction_tag.get_debit_in_base_currency()
            context['totals_by_year'].append(trans_year)


        if period_id:
            accounting_period = AccountingPeriod.objects.get(pk=period_id)
            context['period'] = accounting_period
            context['transactiontags'] = transaction_tags.filter(transaction__date__gte=accounting_period.start_date,
                                                                transaction__date__lte=accounting_period.end_date,).order_by('-transaction__date')
        else:
            context['transactiontags'] = transaction_tags.order_by('-transaction__date')
        return context
