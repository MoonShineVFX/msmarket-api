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
    success_payment = models.OneToOneField(
        "NewebpayPayment", related_name="success_order", on_delete=models.PROTECT, null=True)

    products = models.ManyToManyField(Product, related_name="orders")
    merchant_order_no = models.CharField(max_length=30)
    status = models.IntegerField(default=0)
    amount = models.DecimalField(max_digits=10, decimal_places=4)
    item_count = models.IntegerField(default=0)
    invoice_number = models.CharField(max_length=10, null=True)

    paid_at = models.DateTimeField(null=True)
    paid_by = models.CharField(max_length=10, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    STATUS = {
        0: "unpaid",
        1: "success",
        2: "fail",
        3: "cancel"
    }
    UNPAID = 0
    SUCCESS = 1
    FAIL = 2
    CANCEL = 3


class NewebpayResponse(models.Model):
    order = models.ForeignKey(Order, null=True, related_name="newebpay_responses", on_delete=models.PROTECT)
    Status = models.CharField(max_length=10)
    MerchantID = models.CharField(max_length=20)
    TradeInfo = models.TextField()
    TradeSha = models.TextField()
    Version = models.CharField(max_length=5)
    is_decrypted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class NewebpayPayment(models.Model):
    order = models.ForeignKey(Order, null=True, related_name="newebpay_payments", on_delete=models.PROTECT)
    encrypted_data = models.OneToOneField(NewebpayResponse, related_name="decrypted_payment", on_delete=models.PROTECT)
    status = models.CharField(max_length=10)
    message = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=4)
    trade_no = models.CharField(max_length=20)
    payment_type = models.CharField(max_length=10)
    pay_time = models.DateTimeField()
    ip = models.CharField(max_length=15)
    escrow_bank = models.CharField(max_length=10, null=True, blank=True)

    objects = models.Manager()


class Invoice(models.Model):
    order = models.OneToOneField(Order, on_delete=models.PROTECT, related_name="invoice")
    payment = models.OneToOneField(NewebpayPayment, on_delete=models.PROTECT, related_name="invoice")

    invoice_trans_no = models.CharField(max_length=20)
    total_amount = models.DecimalField(max_digits=10, decimal_places=4)
    invoice_number = models.CharField(max_length=10)
    random_num = models.CharField(max_length=4)
    check_code = models.CharField(max_length=64)
    barcode = models.CharField(max_length=50)
    qrcode_l = models.CharField(max_length=200)
    qrcode_r = models.CharField(max_length=200)

    created_at = models.DateTimeField(auto_now_add=True)