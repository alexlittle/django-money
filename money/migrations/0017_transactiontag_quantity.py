# Generated by Django 4.2.7 on 2023-12-06 12:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('money', '0016_alter_transaction_sales_tax_rate'),
    ]

    operations = [
        migrations.AddField(
            model_name='transactiontag',
            name='quantity',
            field=models.IntegerField(default=0),
        ),
    ]
