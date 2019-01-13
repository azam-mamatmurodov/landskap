from django import template

from apps.products import models as product_models

register = template.Library()


@register.filter
def cafe_exist(product_id, cafe_id):
    is_exist = product_models.CafeMeals.objects.filter(cafe_id=cafe_id, product_id=product_id).count()
    return is_exist


@register.filter
def modifier_exist(modifier_id, product_id):
    is_exist = product_models.ProductModifier.objects.filter(modifier_id=modifier_id, product_id=product_id).count()
    return is_exist
