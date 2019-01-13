from django.db import models
from django.conf import settings
from django.shortcuts import reverse

from ckeditor.fields import RichTextField
from autoslug.fields import AutoSlugField
from mptt.models import MPTTModel, TreeForeignKey

from apps.users.models import Album, File, Cafe


class ModifierCategory(MPTTModel):
    title = models.CharField(max_length=50, unique=True)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    is_top = models.BooleanField(default=False)
    is_single = models.BooleanField(default=False)
    required = models.BooleanField(default=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL)
    available = models.BooleanField(default=True)

    class MPTTMeta:
        order_insertion_by = ['title']

    class Meta:
        verbose_name = 'Modifier category'
        verbose_name_plural = 'Modifier categories'

    def __str__(self):
        return "{}".format(self.title)


class Modifier(models.Model):
    title = models.CharField(max_length=254)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL)
    slug = AutoSlugField(populate_from='title', unique=True, null=True)
    category = models.ForeignKey(ModifierCategory, null=True, blank=True)
    default = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Modifier'
        verbose_name_plural = 'Modifiers'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('modifiers:modifier_detail', args=[self.pk])