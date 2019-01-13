from django.db import models
from django.conf import settings
from django.shortcuts import reverse

from ckeditor.fields import RichTextField
from autoslug.fields import AutoSlugField
from mptt.models import MPTTModel, TreeForeignKey
from apps.modifiers.models import ModifierCategory

from apps.users.models import Album, File, Cafe


class ProductCategory(MPTTModel):
    name = models.CharField(max_length=50, unique=True)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    is_top = models.BooleanField(default=False)
    icon = models.ImageField(upload_to='product/category/', default='default.png')
    available = models.BooleanField(default=False)

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        verbose_name = 'Product category'
        verbose_name_plural = 'Product categories'

    def __str__(self):
        return "{}".format(self.name)


class ProductImage(models.Model):
    file = models.FileField(upload_to='album/%y/%m/%d', null=True, blank=True, default='default.png')
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='images')

    class Meta:
        verbose_name = 'Product image'
        verbose_name_plural = 'Product images'


class Product(models.Model):
    image = models.FileField(upload_to='products/%y/%m/%d', null=True, blank=True, default='default.png')
    title = models.CharField(max_length=254)
    description = models.TextField()
    available = models.BooleanField(default=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL)
    slug = AutoSlugField(populate_from='title', unique=True, null=True)
    category = models.ForeignKey(ProductCategory, null=True, blank=True)
    price = models.DecimalField(max_digits=100, decimal_places=2)
    modifier = models.ForeignKey(ModifierCategory, on_delete=models.CASCADE, related_name='meals')

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('products:product_detail', args=[self.pk])


class Size(models.Model):
    title = models.CharField(max_length=254)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    product = models.ForeignKey(Product, null=False, blank=True)
    default = models.BooleanField(default=False)
    available = models.BooleanField(default=True)


class CafeMeals(models.Model):
    cafe = models.ForeignKey(Cafe, on_delete=models.CASCADE, related_name='meals')
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='cafes')

    class Meta:
        verbose_name = 'Cafe product'
        verbose_name_plural = 'Cafe products'


class ProductModifier(models.Model):
    modifier = models.ForeignKey(ModifierCategory, on_delete=models.CASCADE, related_name='products')
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='modifiers')

    class Meta:
        verbose_name = 'Product modifier'
        verbose_name_plural = 'Product modifiers'
