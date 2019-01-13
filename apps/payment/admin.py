from django.contrib import admin

from apps.payment import models as payment_models


class StripeTransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'payer', 'amount', 'created_at', 'order', 'payment_type', 'status', ]
    list_filter = ['status', 'created_at', ]


class PaypalTransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_customer', 'amount', 'created_at', 'payment_type']
    list_filter = ['created_at', ]

    @staticmethod
    def get_customer(obj):
        return obj.order.customer.get_full_name()


admin.site.register(payment_models.StripeTransaction, StripeTransactionAdmin)
admin.site.register(payment_models.PaypalTransaction, PaypalTransactionAdmin)
