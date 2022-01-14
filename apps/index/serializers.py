# -*- coding: utf-8 -*-
from rest_framework import serializers
from django.conf import settings
from ..product.serializers import ProductListSerializer
from ..user.serializers import EditorBaseSerializer
from .models import Product, Tutorial, AboutUs


class BannerProductSerializer(ProductListSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'title', 'description', 'imgUrl', 'price', 'status')

    def get_status(self, instance):
        return ""


class AboutUsSerializer(serializers.ModelSerializer):
    imgUrl = serializers.SerializerMethodField()
    supportModels = serializers.IntegerField(source="model_count")
    supportFormats = serializers.IntegerField(source="format_count")
    supportRenders = serializers.IntegerField(source="render_count")

    class Meta:
        model = AboutUs
        fields = ('title', 'description', 'imgUrl', 'supportModels', 'supportFormats', 'supportRenders')

    def get_imgUrl(self, instance):
        return "{}/{}".format(settings.IMAGE_ROOT, instance.image) if instance.image else None


class AdminAboutUsSerializer(AboutUsSerializer, EditorBaseSerializer):
    file = serializers.ImageField(write_only=True, source="image")

    class Meta:
        model = AboutUs
        fields = ('title', 'description', 'imgUrl', 'file', 'supportModels', 'supportFormats', 'supportRenders',
                  "createTime", "updateTime", "creator", "updater")


class TutorialSerializer(serializers.ModelSerializer):
    imgUrl = serializers.SerializerMethodField()

    class Meta:
        model = Tutorial
        fields = ('id', 'title', 'description', 'imgUrl')

    def get_imgUrl(self, instance):
        return "{}/{}".format(settings.IMAGE_ROOT, instance.image) if instance.image else None


class TutorialLinkSerializer(TutorialSerializer):
    class Meta:
        model = Tutorial
        fields = ('id', 'title', 'link', 'imgUrl')

