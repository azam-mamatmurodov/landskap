# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-08-11 09:52
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0007_auto_20180809_1913'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='MealCategory',
            new_name='ProductCategory',
        ),
    ]