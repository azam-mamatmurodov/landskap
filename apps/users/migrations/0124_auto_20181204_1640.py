# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-12-04 11:40
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0123_cafegeneralsettings_tax'),
    ]

    operations = [
        migrations.RenameField(
            model_name='cafegeneralsettings',
            old_name='tax',
            new_name='tax_rate',
        ),
    ]