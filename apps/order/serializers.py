# -*- coding: utf-8 -*-
from django.db.models import Q
from django.conf import settings
from rest_framework import serializers
from .models import Cart
from ..product.models import Product
from ..user.models import User


class CartProductListSerializer(serializers.ModelSerializer):
    imgUrl = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ('id', 'title', 'imgUrl', 'price')

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