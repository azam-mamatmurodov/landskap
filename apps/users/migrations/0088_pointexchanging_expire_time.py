# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-08-25 11:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0087_auto_20180825_1611'),
    ]

    operations = [
        migrations.AddField(
            model_name='pointexchanging',
            name='expire_time',
            field=models.DateTimeField(null=True),
        ),
    ]