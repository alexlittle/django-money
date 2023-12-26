import datetime
from django import forms
from dateutil.relativedelta import relativedelta

from money.models import InvoiceTemplate


def set_due_date():
    now = datetime.datetime.now()
    next_month = now + relativedelta(months=1)
    return datetime.datetime(next_month.year, next_month.month, 2)

def set_title():
    now = datetime.datetime.now()
    next_month = now + relativedelta(months=1)
    desc = "Palvelupaketti {month}/{year} (service fee)".format(month=next_month.month, year=next_month.year)
    return desc

class InvoicesForm(forms.Form):
    issue_date = forms.CharField(max_length=100, initial=datetime.datetime.now().strftime('%d.%m.%Y') )
    due_date = forms.CharField(max_length=100, initial=set_due_date().strftime('%d.%m.%Y'))
    title = forms.CharField(max_length=100, initial = set_title())
    ref_nos = forms.CharField(max_length=200)
    send_to = forms.ModelMultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                             queryset=InvoiceTemplate.objects.filter(active=True))


