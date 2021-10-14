# -*- coding: utf-8 -*-
from django.conf import settings
from rest_framework import serializers
from .models import Product, Format, Renderer
from ..serializers import EditorBaseSerializer


class FormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Format
        fields = '__all__'


class RendererSerializer(serializers.ModelSerializer):
    class Meta:
        model = Renderer
        fields = '__all__'


class RelativeProductSerializer(serializers.ModelSerializer):
    imgUrl = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'title', 'imgUrl', 'status')

    def get_imgUrl(self, instance):
        return "{}/{}".format(settings.IMAGE_ROOT, instance.image) if instance.image else None


class ProductListSerializer(EditorBaseSerializer):
    imgUrl = serializers.SerializerMethodField()
    modelSum = serializers.IntegerField(source="model_count")
    fileSize = serializers.SerializerMethodField()
    perImgSize = serializers.IntegerField(source="texture_size")

    tags = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    formats = FormatSerializer(read_only=True)
    renderers = RendererSerializer(read_only=True)
    relativeProducts = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'title', 'price', 'imgUrl', 'modelSum', 'fileSize', 'perImgSize', 'tags',
                  'formats', 'renderers', 'images', 'relativeProducts',
                  'createTime', 'updateTime', 'creator', 'updater')

    def get_imgUrl(self, instance):
        return "{}/{}".format(settings.IMAGE_ROOT, instance.image) if instance.image else None

    def get_fileSize(self, instance):
        pass
        #return instance.model_set.all()[0].size if instance.model_set else None

    def get_relativeProducts(self, instance):
        products = Product.objects.filter(**{})
        return RelativeProductSerializer(products, many=True).data