# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-02-15 14:06
from __future__ import unicode_literals

from django.db import migrations, models
import users.models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_auto_20170109_1449'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='club',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET(users.models.get_national_club), related_name='users', to='clubs.Club'),
        ),
    ]
