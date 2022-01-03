# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from rest_framework import serializers
from .models import Order, Cart, NewebpayResponse, NewebpayPayment
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
        return "{}/{}".format(settings.IMAGE_ROOT, instance.product.preview) if instance.product.preview else None

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


class NewebpayPaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = NewebpayPayment
        fields = '__all__'


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
    account = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ('id', 'orderNumber', 'price', 'account', 'status', 'invoice',
                  'createdAt', 'paidAt', 'paidBy')

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
    orderNumber = serializers.CharField(source="merchant_order_no", allow_null=True)
    account = serializers.CharField(source="email", allow_null=True)
    invoice = serializers.CharField(source="invoice_number", allow_null=True)
    startDate = serializers.DateField(source="start_date", allow_null=True)
    endDate = serializers.DateField(source="end_date", allow_null=True)