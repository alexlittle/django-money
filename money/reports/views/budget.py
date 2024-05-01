from django.views.generic.list import ListView
from django.views.generic import TemplateView
from django.db.models import Sum

from money.models import AccountingPeriod, Transaction, TransactionTag

class BudgetView(ListView):
    template_name = 'money/reports/budget.html'

    def get_queryset(self):
        return AccountingPeriod.objects.filter(active=True).order_by('-start_date')


class BudgetByPeriodView(TemplateView):
    template_name = 'money/reports/budget_by_period.html'

    def get_expenses(self, query, tag):
         transactions = query.filter(transactiontag__tag__name=tag)
         trans_ids = list(transactions.values_list('id', flat=True))
         total = transactions.aggregate(total=Sum("debit"))['total'] if transactions.aggregate(total=Sum("debit"))['total'] else 0
         return total, trans_ids


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        period_id = kwargs['period_id']
        accounting_period = AccountingPeriod.objects.get(pk=period_id)

        # Income
        income_transactions = TransactionTag.objects.filter(transaction__date__gte=accounting_period.start_date,
                                                         transaction__date__lte=accounting_period.end_date,
                                                            allocation_credit__gt=0) \
                                    .exclude(transaction__payment_type="Transfer") \
                                    .exclude(tag__name="kollektiivi")

        income_groups = income_transactions.values("tag__category").distinct()
        income = {}
        income_total = 0
        for ig in income_groups:
            group_income_total = 0
            group_transactions = income_transactions.filter(tag__category=ig['tag__category'])
            for gt in group_transactions:
                group_income_total = group_income_total + gt.get_credit_in_base_currency()
            income_total = income_total + group_income_total
            income[ig['tag__category']] = group_income_total

        expense_transactions = TransactionTag.objects.filter(transaction__date__gte=accounting_period.start_date,
                                                             transaction__date__lte=accounting_period.end_date,
                                                             allocation_debit__gt=0) \
            .exclude(transaction__payment_type__in=("Transfer", "Cashpoint")) \
            .exclude(tag__name="kollektiivi")
        # Personal Expenses
        personal_expenses = []
        personal_expenses_total = 0
        # House & personal
        personal_transactions = expense_transactions.filter(tag__category__in=("house","personal"))
        personal_expenses_tags = personal_transactions.values("tag__name", "tag__id").distinct().order_by('tag__name')
        for pet in personal_expenses_tags:
            p_expense = {}
            tag_expense_total = 0
            group_transactions = personal_transactions.filter(tag__name=pet['tag__name'])
            for gt in group_transactions:
                tag_expense_total = tag_expense_total + gt.get_debit_in_base_currency()
            personal_expenses_total = personal_expenses_total + tag_expense_total
            p_expense['name'] = pet['tag__name']
            p_expense['total'] = tag_expense_total
            p_expense['id'] = pet['tag__id']
            personal_expenses.append(p_expense)

        # Car
        car_transactions = expense_transactions.filter(tag__category="car")
        car_total = 0
        for ct in car_transactions:
            car_total = car_total + ct.get_debit_in_base_currency()
        personal_expenses.append({'name': "car", 'total': car_total})
        personal_expenses_total = personal_expenses_total + car_total

        # Travel
        travel_transactions = expense_transactions.filter(tag__category="travel")
        travel_total = 0
        for tt in travel_transactions:
            travel_total = travel_total + tt.get_debit_in_base_currency()
        personal_expenses.append({'name': "travel", 'total': travel_total})
        personal_expenses_total = personal_expenses_total + travel_total

        # Misc
        misc_transactions = expense_transactions.filter(tag__category="misc")
        misc_total = 0
        for mt in misc_transactions:
            misc_total = misc_total + mt.get_debit_in_base_currency()
        personal_expenses.append({'name': "misc", 'total': misc_total})
        personal_expenses_total = personal_expenses_total + misc_total

        # Business Expenses
        business_expenses = []
        business_expenses_total = 0
        business_transactions = expense_transactions.filter(tag__category__in=("business", "design", "rental"))
        business_expenses_tags = business_transactions.values("tag__name", "tag__id").distinct().order_by('tag__name')
        for bet in business_expenses_tags:
            b_expense = {}
            tag_expense_total = 0
            group_transactions = business_transactions.filter(tag__name=bet['tag__name'])
            for gt in group_transactions:
                tag_expense_total = tag_expense_total + gt.get_debit_in_base_currency()
            business_expenses_total = business_expenses_total + tag_expense_total
            b_expense['name'] = bet['tag__name']
            b_expense['total'] = tag_expense_total
            b_expense['id'] = bet['tag__id']
            business_expenses.append(b_expense)

        context['period'] = accounting_period
        context['income'] = income
        context['income_total'] = income_total

        context['personal_expenses'] = personal_expenses
        context['personal_expenses_total'] = personal_expenses_total

        context['business_expenses'] = business_expenses
        context['business_expenses_total'] = business_expenses_total
        return context