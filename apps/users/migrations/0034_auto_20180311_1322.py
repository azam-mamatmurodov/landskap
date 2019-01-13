# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-03-11 13:22
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0033_auto_20180311_1316'),
    ]

    operations = [
        migrations.AlterField(
            model_name='useravatars',
            name='avatar',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_avatar', to=settings.AUTH_USER_MODEL),
        ),
    ]