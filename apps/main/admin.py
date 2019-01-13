# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib import admin

from apps.main.models import Menu


class MenuAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', ]
    ordering = ('order', )


admin.site.register(Menu, MenuAdmin)
