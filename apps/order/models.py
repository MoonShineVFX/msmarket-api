from django.db import models
from apps.user.models import CreatorBaseModel
from ..product.models import Product
from ..user.models import User


class Cart(models.Model):
    user = models.ForeignKey(
        User, related_name="carts", on_delete=models.PROTECT, null=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    session_key = models.CharField(max_length=40, null=True)    # current length is 32
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()


class Order(models.Model):
    user = models.ForeignKey(
        User, related_name="orders", on_delete=models.PROTECT)

    products = models.ManyToManyField(Product)
    merchant_order_no = models.CharField(max_length=30)
    status = models.IntegerField(default=0)
    amount = models.DecimalField(max_digits=10, decimal_places=4)

    paid_at = models.DateTimeField(null=True)
    paid_by = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()


class NewebpayPayment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT)

    status = models.CharField(max_length=10)
    message = models.CharField(max_length=50)

    amount = models.DecimalField(max_digits=10, decimal_places=4)
    trade_no = models.CharField(max_length=20)
    payment_type = models.CharField(max_length=10)
    pay_time = models.DateTimeField()
    ip = models.CharField(max_length=15)
    EscrowBank = models.CharField(max_length=10, null=True, blank=True)

    json = models.TextField()

    objects = models.Manager()