from django.views.generic.list import ListView
from django.views.generic import TemplateView
from django.db.models import Sum

from money.models import AccountingPeriod, Transaction, TransactionTag

class BudgetView(ListView):
    template_name = 'money/reports/budget.html'
    model = AccountingPeriod


class BudgetByPeriodView(TemplateView):
    template_name = 'money/reports/budget_by_period.html'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        period_id = kwargs['period_id']
        accounting_period = AccountingPeriod.objects.get(pk=period_id)

        # Personal - Income
        personal_income = {'DC-Income': 0,
                           'DesignShop': 0,
                           'MiscIncome': 0,
                           'HouseRental': 0,
                           'RoomRental': 0 }

        dc_income = Transaction.objects.filter(transactiontag__tag__name='dc-income',
                                               date__gte=accounting_period.start_date,
                                               date__lte=accounting_period.end_date).aggregate(total=Sum("credit"))
        personal_income['DC-Income'] = dc_income['total'] if dc_income['total'] else 0

        design_shop = TransactionTag.objects.filter(tag__name__in=('bookmarks', 'kitchen', 'pens', 'rings'),
                                               transaction__date__gte=accounting_period.start_date,
                                               transaction__date__lte=accounting_period.end_date).aggregate(total=Sum("allocation_credit"))
        personal_income['DesignShop'] = design_shop['total'] if design_shop['total'] else 0

        misc_income = Transaction.objects.filter(transactiontag__tag__name__in=('misc income', 'coins', 'misc'),
                                               date__gte=accounting_period.start_date,
                                               date__lte=accounting_period.end_date)
        total = 0
        for mi in misc_income:
            total = total + mi.get_credit_in_base_currency()
        personal_income['MiscIncome'] = total

        house_rental = Transaction.objects.filter(transactiontag__tag__name='northampton house',
                                                 date__gte=accounting_period.start_date,
                                                 date__lte=accounting_period.end_date)
        total = 0
        for mi in house_rental:
            total = total + mi.get_credit_in_base_currency()
        personal_income['HouseRental'] = total

        room_rental = Transaction.objects.filter(transactiontag__tag__name='room-rental',
                                                 date__gte=accounting_period.start_date,
                                                 date__lte=accounting_period.end_date).aggregate(total=Sum("credit"))
        personal_income['RoomRental'] = room_rental['total'] if room_rental['total'] else 0

        personal_income_total = 0
        for key, value in personal_income.items():
            personal_income_total = personal_income_total + value

        income_transactions = Transaction.objects.filter(account__active=True,
                                                 account__type="Cash",
                                                 date__gte=accounting_period.start_date,
                                                 date__lte=accounting_period.end_date,
                                                credit__gt=0) \
                        .exclude(payment_type="Transfer") \
                        .exclude(transactiontag__tag__name="kollektiivi")

        income_total = 0
        for i in income_transactions:
            income_total = income_total + i.get_credit_in_base_currency()

        # Personal - Expenses
        personal_expenses = {'Insurance': 0,
                             'Car': 0,
                             'Rubbish': 0,
                             'Water': 0,
                             'Electric': 0,
                             'PhoneInternet': 0,
                             'Renovations': 0,
                             'Entertainment': 0,
                             'HouseTaxRent': 0,
                             'Travel': 0,
                             'Food': 0,
                             'Gear': 0,
                             'Boat': 0,
                             'GiftTax': 0,
                             'SafetyDepositBox': 0}

        ins = Transaction.objects.filter(transactiontag__tag__name='insurance',
                                                 date__gte=accounting_period.start_date,
                                                 date__lte=accounting_period.end_date).aggregate(total=Sum("debit"))
        personal_expenses['Insurance'] = ins['total'] if ins['total'] else 0

        car = Transaction.objects.filter(transactiontag__tag__category='car',
                                         date__gte=accounting_period.start_date,
                                         date__lte=accounting_period.end_date).aggregate(total=Sum("debit"))
        personal_expenses['Car'] = car['total'] if car['total'] else 0

        rubbish = Transaction.objects.filter(transactiontag__tag__name='rubbish',
                                         date__gte=accounting_period.start_date,
                                         date__lte=accounting_period.end_date).aggregate(total=Sum("debit"))
        personal_expenses['Rubbish'] = rubbish['total'] if rubbish['total'] else 0

        water = Transaction.objects.filter(transactiontag__tag__name='water',
                                             date__gte=accounting_period.start_date,
                                             date__lte=accounting_period.end_date).aggregate(total=Sum("debit"))
        personal_expenses['Water'] = water['total'] if water['total'] else 0

        electric = Transaction.objects.filter(transactiontag__tag__name='electric',
                                           date__gte=accounting_period.start_date,
                                           date__lte=accounting_period.end_date).aggregate(total=Sum("debit"))
        personal_expenses['Electric'] = electric['total'] if electric['total'] else 0

        internet = Transaction.objects.filter(transactiontag__tag__name='phone/internet',
                                              date__gte=accounting_period.start_date,
                                              date__lte=accounting_period.end_date).aggregate(total=Sum("debit"))
        personal_expenses['PhoneInternet'] = internet['total'] if internet['total'] else 0

        renov = Transaction.objects.filter(transactiontag__tag__name='renovations',
                                                   date__gte=accounting_period.start_date,
                                                   date__lte=accounting_period.end_date).aggregate(total=Sum("debit"))
        personal_expenses['Renovations'] = renov['total'] if renov['total'] else 0

        entertainment = Transaction.objects.filter(transactiontag__tag__name__in=('entertainment','restaurant'),
                                              date__gte=accounting_period.start_date,
                                              date__lte=accounting_period.end_date).aggregate(total=Sum("debit"))
        personal_expenses['Entertainment'] = entertainment['total'] if entertainment['total'] else 0

        housetax = Transaction.objects.filter(transactiontag__tag__name='tax & rent',
                                                   date__gte=accounting_period.start_date,
                                                   date__lte=accounting_period.end_date).aggregate(total=Sum("debit"))
        personal_expenses['HouseTaxRent'] = housetax['total'] if housetax['total'] else 0

        travel = Transaction.objects.filter(transactiontag__tag__category='travel',
                                         date__gte=accounting_period.start_date,
                                         date__lte=accounting_period.end_date).aggregate(total=Sum("debit"))
        personal_expenses['Travel'] = travel['total'] if travel['total'] else 0

        food = Transaction.objects.filter(transactiontag__tag__name='food',
                                              date__gte=accounting_period.start_date,
                                              date__lte=accounting_period.end_date).aggregate(total=Sum("debit"))
        personal_expenses['Food'] = food['total'] if food['total'] else 0

        gear = Transaction.objects.filter(transactiontag__tag__name='gear',
                                          date__gte=accounting_period.start_date,
                                          date__lte=accounting_period.end_date).aggregate(total=Sum("debit"))
        personal_expenses['Gear'] = gear['total'] if gear['total'] else 0

        boat = Transaction.objects.filter(transactiontag__tag__name='boat',
                                          date__gte=accounting_period.start_date,
                                          date__lte=accounting_period.end_date).aggregate(total=Sum("debit"))
        personal_expenses['Boat'] = boat['total'] if boat['total'] else 0

        gifttax = Transaction.objects.filter(transactiontag__tag__name='gift-tax',
                                          date__gte=accounting_period.start_date,
                                          date__lte=accounting_period.end_date).aggregate(total=Sum("debit"))
        personal_expenses['GiftTax'] = gifttax['total'] if gifttax['total'] else 0

        safety_deposit = Transaction.objects.filter(transactiontag__tag__name='safety-deposit',
                                             date__gte=accounting_period.start_date,
                                             date__lte=accounting_period.end_date).aggregate(total=Sum("debit"))
        personal_expenses['SafetyDepositBox'] = safety_deposit['total'] if safety_deposit['total'] else 0

        personal_expenses_total = 0
        for key, value in personal_expenses.items():
            personal_expenses_total = personal_expenses_total + value

        expense_transactions = Transaction.objects.filter(account__id__in=(48, 19, 39),
                                                         date__gte=accounting_period.start_date,
                                                         date__lte=accounting_period.end_date,
                                                         debit__gt=0) \
                            .exclude(payment_type="Transfer")

        expense_total = 0
        for i in expense_transactions:
            expense_total = expense_total + i.get_debit_in_base_currency()

        missing_expenses = expense_transactions.exclude(transactiontag__tag__name__in=('food',
                                                                                       'tax & rent',
                                                                                       'entertainment',
                                                                                       'restaurant',
                                                                                       'renovations',
                                                                                       'phone/internet',
                                                                                       'insurance',
                                                                                       'rubbish',
                                                                                       'water',
                                                                                       'electric',
                                                                                       'gear',
                                                                                       'boat',
                                                                                       'gift-tax',
                                                                                       'safety-deposit')) \
                                     .exclude(transactiontag__tag__category__in=('car','travel'))

        for et in missing_expenses:
            print(et.description)
            print(et.debit)
            print(et.id)


        # Business - Income

        # Business - Expenses


        context['period'] = accounting_period

        context['personal_income'] = personal_income
        context['personal_income_total'] = personal_income_total
        context['income_total'] = income_total
        context['income_difference'] = personal_income_total - income_total

        context['personal_expenses_total'] = personal_expenses_total
        context['personal_expenses'] = personal_expenses
        context['expense_total'] = expense_total
        context['expense_difference'] = personal_expenses_total - expense_total

        return context