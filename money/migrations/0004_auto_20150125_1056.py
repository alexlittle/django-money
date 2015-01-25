# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('money', '0003_auto_20150125_1051'),
    ]

    operations = [
        migrations.AlterField(
            model_name='regularpayment',
            name='credit',
            field=models.DecimalField(default=0, max_digits=20, decimal_places=2),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='regularpayment',
            name='debit',
            field=models.DecimalField(default=0, max_digits=20, decimal_places=2),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='transaction',
            name='credit',
            field=models.DecimalField(default=0, max_digits=20, decimal_places=2),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='transaction',
            name='debit',
            field=models.DecimalField(default=0, max_digits=20, decimal_places=2),
            preserve_default=True,
        ),
    ]
