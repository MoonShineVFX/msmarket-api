# -*- coding: utf-8 -*-
from django.db.models import Q
from django.conf import settings
from rest_framework import serializers
from .models import Product, Format, Renderer, Model, Image
from ..serializers import EditorBaseSerializer
from ..category.serializers import TagNameOnlySerializer


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


class WebImageSerializer(ImageUrlSerializer):
    positionId = serializers.IntegerField(source="position_id")
    name = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ('id', 'url', "positionId", "name", "size")

    def get_name(self, instance):
        return instance.file.__str__().rsplit('/', 1)[1] if instance.file else None


class PreviewSerializer(WebImageSerializer):
    class Meta:
        model = Image
        fields = ('id', 'url', "name", "size")


class ImgUrlMixin(serializers.ModelSerializer):
    imgUrl = serializers.SerializerMethodField()

    def get_imgUrl(self, instance):
        return "{}/{}".format(settings.IMAGE_ROOT, instance.thumb_image.file) if instance.thumb_image else None


class ProductListSerializer(ImgUrlMixin):
    price = serializers.IntegerField()
    isActive = serializers.BooleanField(source="is_active")

    class Meta:
        model = Product
        fields = ('id', 'title', 'imgUrl', 'price', 'isActive')


class OrderProductSerializer(ProductListSerializer):
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


class ProductDetailSerializer(ImgUrlMixin):
    price = serializers.IntegerField()
    modelSum = serializers.IntegerField(source="model_count")
    fileSize = serializers.IntegerField(source="model_size")
    perImgSize = serializers.IntegerField(source="texture_size")

    tags = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    models = ModelSerializer(many=True)
    previews = serializers.SerializerMethodField()
    relativeProducts = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'title', "description", 'price', 'imgUrl', 'modelSum', 'fileSize', 'perImgSize', 'tags',
                  'models', 'previews', 'relativeProducts')

    def get_relativeProducts(self, instance):
        products = Product.objects.filter(~Q(id=instance.id), tags__in=instance.tags.all())[:4]
        return ProductListSerializer(products, many=True).data

    def get_previews(self, instance):
        previews = [image for image in instance.images.all() if image.position_id == Image.PREVIEW]
        return PreviewSerializer(previews, many=True).data


class MyProductSerializer(ImgUrlMixin):
    fileSize = serializers.IntegerField(source="model_size")
    models = ModelSerializer(many=True)

    class Meta:
        model = Product
        fields = ('id', 'title', 'imgUrl', 'fileSize', 'models')


class AdminProductListSerializer(ProductListSerializer, EditorBaseSerializer):
    activeTime = serializers.SerializerMethodField()
    inactiveTime = serializers.SerializerMethodField()
    tags = TagNameOnlySerializer(many=True)

    class Meta:
        model = Product
        fields = ('id', 'title', 'imgUrl', 'price', 'isActive', 'tags', 'activeTime', 'inactiveTime')

    def get_activeTime(self, instance):
        return instance.active_at if instance.active_at else ""

    def get_inactiveTime(self, instance):
        return instance.inactive_at if instance.inactive_at else ""


class AdminProductDetailSerializer(ProductDetailSerializer, EditorBaseSerializer):
    isActive = serializers.BooleanField(source="is_active")
    webImages = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'title', "description", 'price', 'imgUrl', 'modelSum', 'fileSize', 'perImgSize', 'tags',
                  'isActive', 'webImages', 'previews')

    def get_webImages(self, instance):
        web_images = [instance.main_image, instance.mobile_main_image, instance.thumb_image, instance.extend_image]
        web_images = filter(None, web_images)
        return WebImageSerializer(web_images, many=True).data

