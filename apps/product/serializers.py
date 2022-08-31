# -*- coding: utf-8 -*-
import datetime
from django.utils import timezone
from django.db.models import Q
from django.conf import settings
from rest_framework import serializers
from .models import Product, Format, Renderer, Model, Image
from ..serializers import EditorBaseSerializer, CreatorBaseSerializer
from ..category.serializers import TagNameOnlySerializer


class FormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Format
        fields = '__all__'


class RendererSerializer(serializers.ModelSerializer):
    class Meta:
        model = Renderer
        fields = '__all__'


class ImageUploadSerializer(serializers.ModelSerializer):
    productId = serializers.IntegerField(source="product_id", write_only=True)
    positionId = serializers.IntegerField(source="position_id")
    file = serializers.ImageField(write_only=True)
    url = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ("id", "productId", 'positionId', "url", "name", "size", "file")
        read_only_fields = ["id", "size"]

    def validate(self, data):
        """
        判斷product同位置是否已機有圖片
        """
        position_id = data['position_id']
        if position_id in Image.position_2_field:
            if Product.objects.filter(id=data['product_id']
                                      ).exclude(**{Image.position_2_field[position_id]+"_id": None}).exists():
                raise serializers.ValidationError("Image at the position of the product already exists")
        return data

    def create(self, validated_data):
        upload_file = validated_data['file']
        validated_data['size'] = upload_file.size
        image = super().create(validated_data)

        position_id = validated_data['position_id']
        if position_id in Image.position_2_field:
            Product.objects.filter(
                id=validated_data['product_id']).update(**{Image.position_2_field[position_id]: image.id})
        return image

    def get_url(self, instance):
        return "{}/{}".format(settings.IMAGE_ROOT, instance.file) if instance.file else None

    def get_name(self, instance):
        return instance.file.__str__().rsplit('/', 1)[1] if instance.file else None


class PreviewListUploadSerializer(serializers.ModelSerializer):
    productId = serializers.IntegerField(source="product_id", write_only=True)
    files = serializers.ListField(
        child=serializers.ImageField(max_length=None, allow_empty_file=False,
                                     use_url=False)
    )

    class Meta:
        model = Image
        fields = ("id", "productId", "files")

    def create(self, validated_data):
        upload_files = validated_data['files']

        for f in upload_files:
            preview = Image.objects.create(
                file=f, size=f.size, product_id=validated_data['product_id'], position_id=Image.PREVIEW,
                creator_id=validated_data['creator_id']
            )
        return preview


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


class ListImgUrlMixin(serializers.ModelSerializer):
    imgUrl = serializers.SerializerMethodField()

    def get_imgUrl(self, instance):
        image = getattr(instance, "thumb_image", None)
        return "{}/{}".format(settings.IMAGE_ROOT, image.file) if image else None


class DetailImgUrlMixin(serializers.ModelSerializer):
    imgUrl = serializers.SerializerMethodField()
    mobileImgUrl = serializers.SerializerMethodField()
    thumb = serializers.SerializerMethodField()

    def get_imgUrl(self, instance):
        image = getattr(instance, "main_image", None)
        return "{}/{}".format(settings.IMAGE_ROOT, image.file) if image else None

    def get_mobileImgUrl(self, instance):
        image = getattr(instance, "mobile_main_image", None)
        return "{}/{}".format(settings.IMAGE_ROOT, image.file) if image else None

    def get_thumb(self, instance):
        image = getattr(instance, "thumb_image", None)
        return "{}/{}".format(settings.IMAGE_ROOT, image.file) if image else None


class ActiveMixin(serializers.ModelSerializer):
    isActive = serializers.BooleanField(source="is_active")
    activeTime = serializers.SerializerMethodField()
    inactiveTime = serializers.SerializerMethodField()

    def get_activeTime(self, instance):
        return instance.active_at if instance.active_at else ""

    def get_inactiveTime(self, instance):
        return instance.inactive_at if instance.inactive_at else ""


class ProductListSerializer(ListImgUrlMixin):
    price = serializers.IntegerField()
    isActive = serializers.BooleanField(source="is_active")

    class Meta:
        model = Product
        fields = ('id', 'title', 'imgUrl', 'price', 'isActive')


class RelativeProductListSerializer(serializers.ModelSerializer):
    price = serializers.IntegerField()
    isActive = serializers.BooleanField(source="is_active")
    imgUrl = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'title', 'imgUrl', 'price', 'isActive')

    def get_imgUrl(self, instance):
        image = getattr(instance, "extend_image", None)
        return "{}/{}".format(settings.IMAGE_ROOT, image.file) if image else None


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


class ModelFilenameSizeSerializer(CreatorBaseSerializer):
    filename = serializers.CharField(source="file")

    class Meta:
        model = Model
        fields = ('id', 'filename', 'size')


class AdminModelSerializer(ModelSerializer, CreatorBaseSerializer):
    filename = serializers.CharField(source="file")
    canDelete = serializers.SerializerMethodField()

    class Meta:
        model = Model
        fields = ('id', 'formatId', 'formatName', 'rendererId', 'rendererName', 'filename', 'size', "canDelete",
                  "createTime", "creator")

    def get_canDelete(self, instance):
        return timezone.now() - instance.created_at > datetime.timedelta(hours=26)


class CreateModelSerializer(serializers.ModelSerializer):
    productId = serializers.IntegerField(source="product_id")
    formatId = serializers.IntegerField(source="format_id")
    rendererId = serializers.IntegerField(source="renderer_id")
    filename = serializers.CharField()

    class Meta:
        model = Model
        fields = ('id', 'productId', 'formatId', 'rendererId', 'size', 'filename')

    def create(self, validated_data):
        filename = validated_data.pop('filename')
        file_path = '/'.join(["products", str(validated_data["product_id"]), "models", filename])
        validated_data["file"] = file_path
        return super().create(validated_data)


class ProductDetailSerializer(DetailImgUrlMixin):
    price = serializers.IntegerField()
    modelSum = serializers.IntegerField(source="model_count")
    fileSize = serializers.IntegerField(source="model_size")
    perImgSize = serializers.CharField(source="texture_size")
    isActive = serializers.BooleanField(source="is_active")

    tags = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    models = ModelSerializer(many=True)
    previews = serializers.SerializerMethodField()
    relativeProducts = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'title', "description", 'price', 'imgUrl', 'mobileImgUrl', 'thumb',
                  'modelSum', 'fileSize', 'perImgSize',
                  'tags', 'isActive', 'models', 'previews', 'relativeProducts')

    def get_relativeProducts(self, instance):
        products = Product.objects.filter(~Q(id=instance.id), tags__in=instance.tags.all()).distinct()[:4]
        return RelativeProductListSerializer(products, many=True).data

    def get_previews(self, instance):
        previews = [image for image in instance.images.all() if image.position_id == Image.PREVIEW]
        return WebImageSerializer(previews, many=True).data


class MyProductSerializer(ListImgUrlMixin):
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
    models = ModelFilenameSizeSerializer(many=True)

    class Meta:
        model = Product
        fields = ('id', 'title', "description", 'price', 'imgUrl', 'modelSum', 'fileSize', 'perImgSize', 'tags',
                  'models', 'isActive', 'webImages', 'previews',
                  "createTime", "updateTime", "creator", "updater")

    def get_webImages(self, instance):
        web_images = [instance.main_image, instance.mobile_main_image, instance.thumb_image, instance.extend_image]
        web_images = filter(None, web_images)
        return WebImageSerializer(web_images, many=True).data


class AdminProductCreateSerializer(serializers.ModelSerializer):
    modelSum = serializers.IntegerField(source="model_count", required=False)
    fileSize = serializers.IntegerField(source="model_size", required=False)
    perImgSize = serializers.CharField(source="texture_size", required=False)
    isActive = serializers.BooleanField(source="is_active", required=False)

    class Meta:
        model = Product
        fields = ('title', "description", 'price', 'modelSum', 'fileSize', 'perImgSize', 'tags', 'isActive')


class AdminProductActiveSerializer(EditorBaseSerializer, ActiveMixin):
    tags = TagNameOnlySerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ('isActive', 'tags', 'activeTime', 'inactiveTime',
                  "createTime", "updateTime", "creator", "updater")


class ProductXLTNSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('title', 'description', )