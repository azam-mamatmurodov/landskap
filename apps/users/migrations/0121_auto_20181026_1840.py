# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-10-26 13:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0120_auto_20181026_1840'),
    ]

    operations = [
        migrations.AlterField(
            model_name='news',
            name='image',
            field=models.ImageField(default='default.png', upload_to=''),
        ),
    ]