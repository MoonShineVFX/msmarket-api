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
    url = serializers.CharField(source="file")

    class Meta:
        model = Image
        fields = ('id', 'url')


class WebProductListSerializer(serializers.ModelSerializer):
    imgUrl = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'title', 'imgUrl', 'price', 'status')

    def get_imgUrl(self, instance):
        return "{}/{}".format(settings.IMAGE_ROOT, instance.preview) if instance.preview else None


class WebProductDetailSerializer(serializers.ModelSerializer):
    imgUrl = serializers.SerializerMethodField()
    modelSum = serializers.IntegerField(source="model_count")
    fileSize = serializers.IntegerField(source="model_size")
    perImgSize = serializers.IntegerField(source="texture_size")

    tags = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    formats = serializers.SerializerMethodField()
    renderers = RendererSerializer(read_only=True)
    images = ImageUrlSerializer(many=True)
    relativeProducts = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'title', "description", 'price', 'imgUrl', 'modelSum', 'fileSize', 'perImgSize', 'tags',
                  'formats', 'renderers', 'images', 'relativeProducts')

    def get_imgUrl(self, instance):
        return "{}/{}".format(settings.IMAGE_ROOT, instance.preview) if instance.preview else None

    def get_formats(self, instance):
        models = Model.objects.filter(product_id=instance.id).values(
            "format_id", "format__name", "renderer_id", "renderer__name").order_by("format_id").all()
        formats = {}
        for model in models:
            if model["format_id"] not in formats:
                formats[model["format_id"]] = {
                    "id": model["format_id"],
                    "label": model["format__name"],
                    "renderers": []
                }
            formats[model["format_id"]]["renderers"].append(
                {
                    "id": model["renderer_id"],
                    "label": model["renderer__name"]
                })
        return [value for key, value in formats.items()]

    def get_relativeProducts(self, instance):
        products = Product.objects.filter(~Q(id=instance.id), tags__in=instance.tags.all())[:4]
        return WebProductListSerializer(products, many=True).data