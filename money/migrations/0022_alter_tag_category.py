# Generated by Django 5.0.4 on 2024-05-01 06:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('money', '0021_alter_tag_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tag',
            name='category',
            field=models.CharField(blank=True, choices=[('travel', 'Travel'), ('house', 'House'), ('kollektiivi', 'Kollektiivi'), ('car', 'Car'), ('personal', 'Personal'), ('misc', 'Misc'), ('business', 'Business'), ('design', 'DesignShop'), ('rental', 'Rental')], max_length=100, null=True),
        ),
    ]
