# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('money', '0006_auto_20150726_0954'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='account',
            name='current',
        ),
        migrations.RemoveField(
            model_name='account',
            name='pension',
        ),
        migrations.AlterField(
            model_name='account',
            name='type',
            field=models.CharField(default=b'cash', max_length=100, choices=[(b'cash', b'Cash'), (b'invest', b'Investment'), (b'property', b'Property'), (b'pension', b'Pension')]),
            preserve_default=True,
        ),
    ]
