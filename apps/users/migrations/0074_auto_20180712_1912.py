# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-07-12 14:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0073_auto_20180712_1738'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cafe',
            name='call_center',
            field=models.CharField(max_length=13, verbose_name='Phone'),
        ),
    ]