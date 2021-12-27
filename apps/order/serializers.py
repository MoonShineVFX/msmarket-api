# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from rest_framework import serializers
from .models import Order, Cart, NewebpayResponse
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


class OrderSerializer(serializers.ModelSerializer):
    orderNumber = serializers.CharField(source="merchant_order_no")
    price = serializers.IntegerField(source="amount")
    totalItems = serializers.IntegerField(source="item_count")
    createdAt = serializers.DateTimeField(source="created_at")
    paidAt = serializers.DateTimeField(source="paid_at")
    paidBy = serializers.CharField(source="paid_by")

    invoice = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ('id', 'orderNumber', 'price', 'status', 'totalItems', 'invoice',
                  'createdAt', 'paidAt', 'paidBy')

    def get_invoice(self, instance):
        try:
            return instance.invoice.invoice_number
        except ObjectDoesNotExist:
            return None

    def get_status(self, instance):
        return Order.STATUS[instance.status]


class OrderDetailSerializer(OrderSerializer):
    products = OrderProductSerializer(many=True)

    class Meta:
        model = Order
        fields = ('id', 'orderNumber', 'price', 'status', 'totalItems', 'invoice',
                  'createdAt', 'paidAt', 'paidBy', 'products')