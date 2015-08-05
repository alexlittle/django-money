# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('money', '0005_account_type'),
    ]

    operations = [
        migrations.RenameField(
            model_name='account',
            old_name='include',
            new_name='active',
        ),
    ]
