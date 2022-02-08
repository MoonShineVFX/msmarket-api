# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from rest_framework import serializers
from .models import Order, Cart, NewebpayResponse, NewebpayPayment, Invoice, InvoiceError
from ..product.serializers import OrderProductSerializer


class CartProductListSerializer(serializers.ModelSerializer):
    productId = serializers.IntegerField(source="product_id")
    imgUrl = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ('id', 'productId', 'title', 'imgUrl', 'price')

    def get_imgUrl(self, instance):
        return "{}/{}".format(settings.IMAGE_ROOT, instance.product.thumb_image.file) if instance.product.thumb_image else None

    def get_title(self, instance):
        return instance.product.title

    def get_price(self, instance):
        return instance.product.price


class CartAddSerializer(serializers.ModelSerializer):
    productId = serializers.IntegerField(source="product_id")

    class Meta:
        model = Cart
        fields = ('productId', )


class NewebpayResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewebpayResponse
        fields = '__all__'


class EZPayInvoiceSerializer(serializers.ModelSerializer):
    MerchantID = serializers.CharField(max_length=15, source="merchant_id")
    MerchantOrderNo = serializers.CharField(max_length=20, source="invoice_merchant_order_no")
    InvoiceTransNo = serializers.CharField(max_length=20, source="invoice_trans_no")
    TotalAmt = serializers.DecimalField(max_digits=10, decimal_places=4, source="total_amount")
    InvoiceNumber = serializers.CharField(max_length=10, source="invoice_number")
    RandomNum = serializers.CharField(max_length=4, source="random_num")
    CheckCode = serializers.CharField(max_length=64, source="check_code")
    CreateTime = serializers.DateTimeField(source="created_at")
    BarCode = serializers.CharField(max_length=50, source="barcode")
    QRcodeL = serializers.CharField(max_length=200, source="qrcode_l")
    QRcodeR = serializers.CharField(max_length=200, source="qrcode_r")

    class Meta:
        model = Invoice
        fields = ("MerchantID", "MerchantOrderNo", "InvoiceTransNo", "TotalAmt", "InvoiceNumber", "RandomNum",
                  "CheckCode", "CreateTime", "BarCode", "QRcodeL", "QRcodeR")


class EZPayResponseSerializer(serializers.Serializer):
    Status = serializers.CharField(max_length=10, source="status")
    Message = serializers.CharField(max_length=30, source="message")
    Result = serializers.CharField(allow_null=True, required=False)


class NewebpayPaymentSerializer(serializers.ModelSerializer):
    Amt = serializers.DecimalField(max_digits=10, decimal_places=4, source="amount")
    TradeNo = serializers.CharField(max_length=20, source="trade_no")
    PaymentType = serializers.CharField(max_length=10, source="payment_type")
    PayTime = serializers.DateTimeField(source="pay_time")
    IP = serializers.CharField(max_length=15, source="ip")
    EscrowBank = serializers.CharField(max_length=10, allow_null=True, source="escrow_bank")

    class Meta:
        model = NewebpayPayment
        fields = ("Amt", "TradeNo", "PaymentType", "PayTime", "IP", "EscrowBank")


class OrderSerializer(serializers.ModelSerializer):
    orderNumber = serializers.CharField(source="merchant_order_no")
    price = serializers.IntegerField(source="amount")
    totalItems = serializers.IntegerField(source="item_count")
    createdAt = serializers.DateTimeField(source="created_at")

    invoice = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    paidAt = serializers.SerializerMethodField()
    paidBy = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ('id', 'orderNumber', 'price', 'status', 'totalItems', 'invoice',
                  'createdAt', 'paidAt', 'paidBy')

    def get_invoice(self, instance):
        return instance.invoice_number if instance.invoice_number else ""

    def get_status(self, instance):
        return Order.STATUS[instance.status]

    def get_paidAt(self, instance):
        return instance.paid_at if instance.paid_at else ""

    def get_paidBy(self, instance):
        return instance.paid_by if instance.paid_by else ""


class OrderDetailSerializer(OrderSerializer):
    products = OrderProductSerializer(many=True)

    class Meta:
        model = Order
        fields = ('id', 'orderNumber', 'price', 'status', 'totalItems', 'invoice',
                  'createdAt', 'paidAt', 'paidBy', 'products')


class AdminOrderListSerializer(OrderSerializer):
    tradeNumber = serializers.SerializerMethodField()
    account = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ('id', 'orderNumber', 'tradeNumber', 'price', 'account', 'status', 'invoice',
                  'createdAt', 'paidAt', 'paidBy')

    def get_tradeNumber(self, instance):
        return instance.success_payment.trade_no if instance.success_payment else ""

    def get_account(self, instance):
        return instance.user.email


class AdminOrderDetailSerializer(OrderDetailSerializer):
    tradeNumber = serializers.SerializerMethodField()
    account = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ('id', 'orderNumber', 'tradeNumber', 'price', 'account', 'status', 'invoice',
                  'createdAt', 'paidAt', 'paidBy', 'products')

    def get_tradeNumber(self, instance):
        return instance.success_payment.trade_no if instance.success_payment else ""

    def get_account(self, instance):
        return instance.user.email


class AdminOrderSearchParamsSerializer(serializers.Serializer):
    orderNumber = serializers.CharField(source="merchant_order_no", required=False, allow_blank=True)
    account = serializers.EmailField(source="email", required=False, allow_blank=True)
    invoice = serializers.CharField(source="invoice_number", required=False, allow_blank=True)
    startDate = serializers.DateField(source="start_date", required=False)
    endDate = serializers.DateField(source="end_date", required=False)