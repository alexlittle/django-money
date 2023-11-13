# Generated by Django 4.2.7 on 2023-11-13 14:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('money', '0015_transaction_sales_tax_rate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='sales_tax_rate',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=20),
        ),
    ]
