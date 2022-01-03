# -*- coding: utf-8 -*-
from django.db.models import Q
from django.conf import settings
from rest_framework import serializers
from .models import Product, Format, Renderer, Model, Image
from ..serializers import EditorBaseSerializer


class FormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Format
        fields = '__all__'


class RendererSerializer(serializers.ModelSerializer):
    class Meta:
        model = Renderer
        fields = '__all__'


class ImageUrlSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ('id', 'url')

    def get_url(self, instance):
        return "{}/{}".format(settings.IMAGE_ROOT, instance.file) if instance.file else None


class WebProductListSerializer(serializers.ModelSerializer):
    imgUrl = serializers.SerializerMethodField()
    price = serializers.IntegerField()

    class Meta:
        model = Product
        fields = ('id', 'title', 'imgUrl', 'price', 'status')

    def get_imgUrl(self, instance):
        return "{}/{}".format(settings.IMAGE_ROOT, instance.preview) if instance.preview else None


class OrderProductSerializer(WebProductListSerializer):
    class Meta:
        model = Product
        fields = ('id', 'title', 'imgUrl', 'price')


class ModelSerializer(serializers.ModelSerializer):
    formatId = serializers.IntegerField(source="format_id")
    formatName = serializers.SerializerMethodField()
    rendererId = serializers.IntegerField(source="renderer_id")
    rendererName = serializers.SerializerMethodField()

    class Meta:
        model = Model
        fields = ('id', 'formatId', 'formatName', 'rendererId', 'rendererName', 'size')

    def get_formatName(self, instance):
        return instance.format.name

    def get_rendererName(self, instance):
        return instance.renderer.name


class WebProductDetailSerializer(serializers.ModelSerializer):
    price = serializers.IntegerField()
    imgUrl = serializers.SerializerMethodField()
    modelSum = serializers.IntegerField(source="model_count")
    fileSize = serializers.IntegerField(source="model_size")
    perImgSize = serializers.IntegerField(source="texture_size")

    tags = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    models = ModelSerializer(many=True)
    images = ImageUrlSerializer(many=True)
    relativeProducts = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'title', "description", 'price', 'imgUrl', 'modelSum', 'fileSize', 'perImgSize', 'tags',
                  'models', 'images', 'relativeProducts')

    def get_imgUrl(self, instance):
        return "{}/{}".format(settings.IMAGE_ROOT, instance.preview) if instance.preview else None

    def get_relativeProducts(self, instance):
        products = Product.objects.filter(~Q(id=instance.id), tags__in=instance.tags.all())[:4]
        return WebProductListSerializer(products, many=True).data


class MyProductSerializer(serializers.ModelSerializer):
    imgUrl = serializers.SerializerMethodField()
    fileSize = serializers.IntegerField(source="model_size")
    models = ModelSerializer(many=True)

    class Meta:
        model = Product
        fields = ('id', 'title', 'imgUrl', 'fileSize', 'models')

    def get_imgUrl(self, instance):
        return "{}/{}".format(settings.IMAGE_ROOT, instance.preview) if instance.preview else None