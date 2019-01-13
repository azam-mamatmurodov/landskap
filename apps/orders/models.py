import uuid
from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_save
from django.utils.translation import ugettext as _
from django.conf import settings

from apps.products.models import Product, Cafe
from project import modules as project_modules
from apps.modifiers import models as modifier_models


class Order(models.Model):
    NEW = 'new'
    READY = 'ready'
    REJECT = 'reject'

    ORDER_STATUS = (
        (NEW, _('New')),
        (READY, _('Ready')),
        (REJECT, _('Reject')),
    )
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='order_customer')
    created = models.DateTimeField(auto_now_add=True, )
    order_unique_id = models.CharField(unique=True, blank=True, null=True, max_length=120, verbose_name=_('Order Id'),
                                       editable=False)
    sub_total_price = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2)
    tax_total = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2)
    total_price = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2)
    state = models.CharField(choices=ORDER_STATUS, default=ORDER_STATUS[0][0], blank=True, max_length=60)
    cafe = models.ForeignKey(Cafe, null=True)
    pre_order = models.BooleanField(default=False)
    pre_order_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return "Order - {}".format(self.pk)

    def get_order_status(self, status_key):
        status_value = status_key
        for status in self.ORDER_STATUS:
            if status[0] == status_key:
                status_value = status[1]
                break
        return status_value

    @property
    def get_status(self):
        return self.ORDER_STATUS[self.state][1]

    def get_items(self):
        return self.cart_items.all()

    @staticmethod
    def get_total_price(obj):
        return obj.total_price * 100

    @staticmethod
    def get_sub_total_price(obj):
        return obj.sub_total_price * 100

    @staticmethod
    def get_tax_total(obj):
        return obj.tax_total * 100

    def get_items_list(self):
        return self.cart_items.values('product__title', 'product', 'count', 'modifiers', 'product__price')


class Cart(models.Model):
    product = models.ForeignKey(Product, related_name='product')
    count = models.IntegerField()
    order = models.ForeignKey(Order, blank=True, null=True, related_name='cart_items')
    is_free = models.BooleanField(default=False)
    price = models.FloatField(default=0)

    class Meta:
        verbose_name = _('Cart item')
        verbose_name_plural = _('Cart items')

    @property
    def get_modifiers(self):
        return CartModifier.objects.filter(cart_id=self.id)

    def __str__(self):
        return "{}".format(self.product)


class CartModifier(models.Model):
    cart = models.ForeignKey(Cart, related_name='modifiers')
    product = models.ForeignKey(Product, related_name='product_modifier')
    order = models.ForeignKey(Order, blank=True, null=True, related_name='cart_order_items')
    modifier = models.ForeignKey(modifier_models.Modifier, blank=True, null=True, related_name='cart_modifier_items')
    price = models.FloatField(default=0)
    count = models.IntegerField()

    class Meta:
        verbose_name = _('Cart modifier item')
        verbose_name_plural = _('Cart modifier items')

    def __str__(self):
        return "{}".format(self.product)


class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, related_name='transaction', )
    created_time = models.DateTimeField(auto_now=True)
    payer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)
    amount = models.FloatField(null=True)
    payment_type = models.CharField(max_length=254, null=True)


def transaction_saver(sender, instance, **kwargs):
    if kwargs['created']:
        cafe = instance.order.cafe
        order = instance.order
        customer = order.customer
        total_count = order.cart_items.filter(is_free=False).aggregate(Sum('count'))
        count__sum = int(total_count['count__sum'])
        project_modules.point_free_item_calculation(cafe=cafe, client=customer, count=count__sum)


post_save.connect(receiver=transaction_saver, sender=Transaction)
