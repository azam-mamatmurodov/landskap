from django.db import models
from django.db.models.signals import post_save

from apps.orders import models as order_models


class StripeTransaction(models.Model):

    payer = models.ForeignKey('users.User')
    created_at = models.DateTimeField(auto_now=True)
    token = models.CharField(max_length=254, null=True)
    customer_id = models.CharField(max_length=254, null=True)
    card_id = models.CharField(max_length=254, null=True)
    amount = models.FloatField()
    payment_id = models.CharField(max_length=254)
    description = models.TextField()
    order = models.ForeignKey('orders.Order')
    payment_type = models.CharField(max_length=254)
    payment_time = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=60, null=True, default='in_process')


def stripe_saver(sender, instance, **kwargs):
    if kwargs['created']:
        order_models.Transaction.objects.create(order=instance.order,
                                                payment_type=instance.payment_type,
                                                amount=instance.amount,
                                                payer=instance.payer)


post_save.connect(sender=StripeTransaction, receiver=stripe_saver)


class PaypalTransaction(models.Model):
    transaction_id = models.TextField(editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    amount = models.FloatField()
    description = models.TextField(null=True, blank=True)
    order = models.ForeignKey('orders.Order')
    payment_type = models.CharField(max_length=254)
    payment_time = models.DateTimeField(auto_now_add=True)
