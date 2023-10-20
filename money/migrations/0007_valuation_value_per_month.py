# Generated by Django 4.2.6 on 2023-10-17 16:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('money', '0006_alter_tag_options_tag_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='valuation',
            name='value_per_month',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=20),
        ),
    ]