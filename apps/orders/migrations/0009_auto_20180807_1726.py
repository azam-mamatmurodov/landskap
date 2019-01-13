# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-08-07 12:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0008_auto_20180804_2012'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='state',
            field=models.CharField(blank=True, choices=[('new', 'New'), ('available', 'Available'), ('resolved', 'Resolved'), ('expired', 'Expired')], default='new', max_length=60),
        ),
    ]