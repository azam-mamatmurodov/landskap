from django.contrib import admin

from apps.modifiers.models import Modifier, ModifierCategory


class ModifierAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'price', 'category', 'owner', ]

    def get_owner(self, obj):
        return obj.get_full_name()


class CafeMealsAdmin(admin.ModelAdmin):
    list_display = ['modifier', 'cafe']


admin.site.register(Modifier, ModifierAdmin)
admin.site.register(ModifierCategory)
