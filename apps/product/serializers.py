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


class UploadImageSerializer(serializers.ModelSerializer):
    productId = serializers.IntegerField(source="product_id", write_only=True)
    positionId = serializers.IntegerField(source="position_id")
    file = serializers.ImageField(write_only=True)
    url = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ("id", "productId", 'positionId', "url", "name", "size", "file")
        read_only_fields = ["id", "size"]

    def create(self, validated_data):
        upload_file = validated_data['file']
        validated_data['size'] = upload_file.size
        return super().create(validated_data)

    def get_url(self, instance):
        return "{}/{}".format(settings.IMAGE_ROOT, instance.file) if instance.file else None

    def get_name(self, instance):
        return instance.file.__str__().rsplit('/', 1)[1] if instance.file else None


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


class ImagePositionTypeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    key = serializers.CharField()
    name = serializers.CharField()


class PreviewSerializer(WebImageSerializer):
    class Meta:
        model = Image
        fields = ('id', 'url', "name", "size")


class ImgUrlMixin(serializers.ModelSerializer):
    imgUrl = serializers.SerializerMethodField()

    def get_imgUrl(self, instance):
        return "{}/{}".format(settings.IMAGE_ROOT, instance.thumb_image.file) if instance.thumb_image else None


class ActiveMixin(serializers.ModelSerializer):
    activeTime = serializers.SerializerMethodField()
    inactiveTime = serializers.SerializerMethodField()

    def get_activeTime(self, instance):
        return instance.active_at if instance.active_at else ""

    def get_inactiveTime(self, instance):
        return instance.inactive_at if instance.inactive_at else ""


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
    perImgSize = serializers.CharField(source="texture_size")

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
        return WebImageSerializer(previews, many=True).data


class MyProductSerializer(ImgUrlMixin):
    fileSize = serializers.IntegerField(source="model_size")
    models = ModelSerializer(many=True)

    class Meta:
        model = Product
        fields = ('id', 'title', 'imgUrl', 'fileSize', 'models')


class AdminProductListSerializer(ProductListSerializer, EditorBaseSerializer, ActiveMixin):
    tags = TagNameOnlySerializer(many=True)

    class Meta:
        model = Product
        fields = ('id', 'title', 'imgUrl', 'price', 'isActive', 'tags', 'activeTime', 'inactiveTime',
                  "createTime", "updateTime", "creator", "updater")


class AdminProductDetailSerializer(ProductDetailSerializer, EditorBaseSerializer):
    isActive = serializers.BooleanField(source="is_active")
    webImages = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'title', "description", 'price', 'imgUrl', 'modelSum', 'fileSize', 'perImgSize', 'tags',
                  'isActive', 'webImages', 'previews',
                  "createTime", "updateTime", "creator", "updater")

    def get_webImages(self, instance):
        web_images = [instance.main_image, instance.mobile_main_image, instance.thumb_image, instance.extend_image]
        web_images = filter(None, web_images)
        return WebImageSerializer(web_images, many=True).data


class AdminProductCreateSerializer(serializers.ModelSerializer):
    modelSum = serializers.IntegerField(source="model_count")
    fileSize = serializers.IntegerField(source="model_size", read_only=True)
    perImgSize = serializers.CharField(source="texture_size")
    isActive = serializers.BooleanField(source="is_active")


    class Meta:
        model = Product
        fields = ('title', "description", 'price', 'modelSum', 'fileSize', 'perImgSize', 'tags', 'isActive')


class AdminProductActiveSerializer(EditorBaseSerializer, ActiveMixin):
    isActive = serializers.BooleanField(source="is_active", allow_null=None, write_only=True)
    tags = TagNameOnlySerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ('isActive', 'tags', 'activeTime', 'inactiveTime',
                  "createTime", "updateTime", "creator", "updater")