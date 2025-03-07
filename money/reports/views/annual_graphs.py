from django.views.generic import TemplateView

from money.models import Transaction


class AnnualGraphsView(TemplateView):

    template_name = 'money/reports/annual_graphs.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = kwargs['year']
        context['year'] = year
        context['transactions'] = Transaction.objects.filter(date__year=year)
        return context