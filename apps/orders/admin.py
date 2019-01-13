from django.contrib import admin

from apps.orders.models import Order, Cart, Transaction


class CartInline(admin.TabularInline):
    model = Cart


class CartAdmin(admin.ModelAdmin):
    list_display = ['product', 'per_item_price', 'count', 'get_order', ]

    def per_item_price(self, obj):
        return "{}".format(obj.product.price)

    per_item_price.short_description = "Price for per item"

    def get_order(self, obj):
        if obj.order:
            return "<a href='/admin/orders/order/%s/change/'>%s</a>" % (obj.order.pk, 'Order - ' + str(obj.order.pk))
        else:
            return None

    get_order.allow_tags = True
    get_order.short_description = 'Order'

    list_display_links = ['product', 'get_order', ]


class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'total_price', 'sub_total_price', 'created', 'state', 'customer', ]
    list_filter = ['state', ]
    list_editable = ['state']
    inlines = [CartInline, ]


class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_time', 'order']
    list_filter = ['created_time', ]


admin.site.register(Order, OrderAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Transaction, TransactionAdmin)
