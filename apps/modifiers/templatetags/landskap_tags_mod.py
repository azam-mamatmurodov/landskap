from django import template

from apps.modifiers import models as modifier_models

register = template.Library()


@register.filter
def cafe_exist(modifier_id, cafe_id):
    is_exist = modifier_models.CafeModifiers.objects.filter(cafe_id=cafe_id, modifier_id=modifier_id).count()
    return is_exist
