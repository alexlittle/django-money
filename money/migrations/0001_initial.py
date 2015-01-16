# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('include', models.BooleanField(default=True)),
                ('current', models.BooleanField(default=True)),
                ('currency', models.CharField(max_length=3, choices=[(b'GBP', b'GBP'), (b'EUR', b'EUR')])),
                ('pension', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ExchangeRate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('from_cur', models.CharField(max_length=3, choices=[(b'GBP', b'GBP'), (b'EUR', b'EUR')])),
                ('to_cur', models.CharField(max_length=3, choices=[(b'GBP', b'GBP'), (b'EUR', b'EUR')])),
                ('date', models.DateTimeField(default=django.utils.timezone.now)),
                ('rate', models.DecimalField(max_digits=20, decimal_places=2)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RegularPayment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=100)),
                ('credit', models.DecimalField(max_digits=20, decimal_places=2)),
                ('debit', models.DecimalField(max_digits=20, decimal_places=2)),
                ('next_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('end_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('payment_type', models.CharField(max_length=15, choices=[(b'VISA', b'Visa'), (b'TRANSFER', b'Transfer'), (b'PAID_IN', b'Paid in'), (b'PAY', b'Pay')])),
                ('account', models.ForeignKey(to='money.Account')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('payment_type', models.CharField(max_length=15, choices=[(b'VISA', b'Visa'), (b'TRANSFER', b'Transfer'), (b'PAID_IN', b'Paid in'), (b'PAY', b'Pay')])),
                ('date', models.DateTimeField(default=django.utils.timezone.now)),
                ('credit', models.DecimalField(max_digits=20, decimal_places=2)),
                ('debit', models.DecimalField(max_digits=20, decimal_places=2)),
                ('on_statement', models.BooleanField(default=False)),
                ('description', models.CharField(max_length=100)),
                ('account', models.ForeignKey(to='money.Account')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Valuation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(default=django.utils.timezone.now)),
                ('value', models.DecimalField(max_digits=20, decimal_places=2)),
                ('account', models.ForeignKey(to='money.Account')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
