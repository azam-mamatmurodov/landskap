# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-12-06 14:05
from __future__ import unicode_literals

from django.db import migrations
from apps.modifiers.models import ModifierCategory


class Migration(migrations.Migration):
    dependencies = [
        ('modifiers', '0001_initial'),
    ]

    # def insert_first_data(apps, schema_editor):
        # modifier_category = ModifierCategory()
        # modifier_category.id = 0
        # modifier_category.name = 'Cheeses'
        # modifier_category.save()

    operations = [
        # migrations.RunPython(insert_first_data)
    ]