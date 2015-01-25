# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('money', '0002_transactiontag'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exchangerate',
            name='rate',
            field=models.DecimalField(max_digits=20, decimal_places=5),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='regularpayment',
            name='payment_type',
            field=models.CharField(max_length=15, choices=[(b'Visa', b'Visa'), (b'Transfer', b'Transfer'), (b'Paid in', b'Paid in'), (b'Pay', b'Pay'), (b'Standing Order', b'Standing Order'), (b'Cheque', b'Cheque'), (b'Interest', b'Interest'), (b'Switch', b'Switch'), (b'Cashpoint', b'Cashpoint'), (b'Direct Debit', b'Direct Debit'), (b'Mastercard', b'Mastercard')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='transaction',
            name='payment_type',
            field=models.CharField(max_length=15, choices=[(b'Visa', b'Visa'), (b'Transfer', b'Transfer'), (b'Paid in', b'Paid in'), (b'Pay', b'Pay'), (b'Standing Order', b'Standing Order'), (b'Cheque', b'Cheque'), (b'Interest', b'Interest'), (b'Switch', b'Switch'), (b'Cashpoint', b'Cashpoint'), (b'Direct Debit', b'Direct Debit'), (b'Mastercard', b'Mastercard')]),
            preserve_default=True,
        ),
    ]
