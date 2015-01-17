# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('money', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TransactionTag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tag', models.ForeignKey(to='money.Tag')),
                ('transaction', models.ForeignKey(to='money.Transaction')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
