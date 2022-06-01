# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from rest_framework import serializers
from .models import Order, Cart, NewebpayResponse, NewebpayPayment, EInvoice, InvoiceError, PaperInvoice
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


class EZPayInvoiceSerializer(serializers.Serializer):
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


class EZPayResponseSerializer(serializers.Serializer):
    Status = serializers.CharField(max_length=10, source="status")
    Message = serializers.CharField(max_length=30, source="message")


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


class OrderCreateSerializer(serializers.Serializer):
    realName = serializers.CharField(max_length=100, source="real_name")
    address = serializers.CharField(max_length=100)
    invoiceType = serializers.CharField(max_length=100, source="invoice_type")
    receiverName = serializers.CharField(max_length=100, source="receiver_name")
    receiverAddress = serializers.CharField(max_length=100, source="receiver_address")
    companyName = serializers.CharField(max_length=100, source="company_name")
    taxNumber = serializers.CharField(max_length=8, source="tax_number")
    paperInvoiceType = serializers.CharField(max_length=20, source="paper_invoice_type")

    def create(self, validated_data):
        type_str = validated_data.pop("invoice_type")
        paper_invoice_type = validated_data.pop("paper_invoice_type")
        validated_data["type"] = PaperInvoice.TYPE_ID[paper_invoice_type]

        if type_str == "paper":
            return PaperInvoice.objects.create(**validated_data)
        else:
            return None


class OrderDetailSerializer(OrderSerializer):
    products = OrderProductSerializer(many=True)

    class Meta:
        model = Order
        fields = ('id', 'orderNumber', 'price', 'status', 'totalItems', 'invoice',
                  'createdAt', 'paidAt', 'paidBy', 'products')


class AdminOrderListSerializer(OrderSerializer):
    tradeNumber = serializers.SerializerMethodField()
    account = serializers.SerializerMethodField()
    invoiceType = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ('id', 'orderNumber', 'tradeNumber', 'price', 'account', 'status', 'invoice', 'invoiceType',
                  'createdAt', 'paidAt', 'paidBy')

    def get_tradeNumber(self, instance):
        return instance.success_payment.trade_no if instance.success_payment else ""

    def get_account(self, instance):
        return instance.user.email

    def get_invoiceType(self, instance):
        return Order.INVOICE_TYPE[instance.invoice_type]


class AdminOrderDetailSerializer(OrderDetailSerializer):
    tradeNumber = serializers.SerializerMethodField()
    account = serializers.SerializerMethodField()
    invoiceType = serializers.SerializerMethodField()
    realName = serializers.CharField(source="paper_invoice.real_name", allow_null=True)
    address = serializers.CharField(source="paper_invoice.address", allow_null=True)
    receiverName = serializers.CharField(source="paper_invoice.receiver_name", allow_null=True)
    receiverAddress = serializers.CharField(source="paper_invoice.receiver_address", allow_null=True)
    companyName = serializers.CharField(source="paper_invoice.company_name", allow_null=True)
    taxNumber = serializers.CharField(source="paper_invoice.tax_number", allow_null=True)
    paperInvoiceType = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ('id', 'orderNumber', 'tradeNumber', 'price', 'account', 'status',
                  'createdAt', 'paidAt', 'paidBy',
                  'realName', 'address', 'invoice', 'invoiceType', 'receiverName', 'receiverAddress',
                  'paperInvoiceType', 'companyName', 'taxNumber',
                  'products')

    def get_tradeNumber(self, instance):
        return instance.success_payment.trade_no if instance.success_payment else ""

    def get_account(self, instance):
        return instance.user.email

    def get_invoiceType(self, instance):
        return Order.INVOICE_TYPE[instance.invoice_type]

    def get_paperInvoiceType(self, instance):
        if instance.paper_invoice:
            return PaperInvoice.TYPE_NAME[instance.paper_invoice.type]
        return None


class AdminOrderSearchParamsSerializer(serializers.Serializer):
    orderNumber = serializers.CharField(source="merchant_order_no", required=False, allow_blank=True)
    account = serializers.EmailField(source="email", required=False, allow_blank=True)
    invoice = serializers.CharField(source="invoice_number", required=False, allow_blank=True)
    startDate = serializers.DateField(source="start_date", required=False)
    endDate = serializers.DateField(source="end_date", required=False)


class AdminOrderPaperInvoiceSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    invoice = serializers.CharField(source="invoice_number")

    class Meta:
        model = Order
        fields = ('id', 'invoice')

    def create(self, validated_data):
        type_str = validated_data.pop("invoice_type")
        if type_str == "paper":
            return PaperInvoice.objects.create(**validated_data)
        else:
            return None