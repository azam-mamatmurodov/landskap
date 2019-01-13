# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class Menu(models.Model):
    title = models.CharField(max_length=120)
    slug = models.CharField(max_length=220)
    order = models.IntegerField(default=0)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return "/{}/".format(self.slug)
