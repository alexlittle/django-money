import datetime

from dateutil.relativedelta import relativedelta
from django import forms

from money.models import InvoiceTemplate


def set_due_date():
    now = datetime.datetime.now()
    next_month = now + relativedelta(months=1)
    return datetime.datetime(next_month.year, next_month.month, 2)


def set_title():
    now = datetime.datetime.now()
    next_month = now + relativedelta(months=1)
    desc = f"Palvelupaketti {next_month.month}/{next_month.year} (service fee)"
    return desc


class InvoicesForm(forms.Form):
    issue_date = forms.CharField(
        max_length=100, initial=datetime.datetime.now().strftime("%d.%m.%Y")
    )
    due_date = forms.CharField(max_length=100, initial=set_due_date().strftime("%d.%m.%Y"))
    title = forms.CharField(max_length=100, initial=set_title())
    ref_nos = forms.CharField(max_length=200)
    send_to = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple, queryset=InvoiceTemplate.objects.filter(active=True)
    )
