from django.contrib import admin

from apps.products.models import Product, ProductImage, CafeMeals, ProductCategory


class ProductImageInline(admin.TabularInline):
    model = ProductImage


class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'price', 'category', 'owner', ]
    inlines = [ProductImageInline]

    def get_owner(self, obj):
        return obj.get_full_name()


class CafeMealsAdmin(admin.ModelAdmin):
    list_display = ['product', 'cafe']


admin.site.register(Product, ProductAdmin)
admin.site.register(CafeMeals, CafeMealsAdmin)
admin.site.register(ProductCategory)
