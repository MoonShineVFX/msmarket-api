# -*- coding: utf-8 -*-
from rest_framework import serializers
from django.conf import settings
from ..product.serializers import ProductListSerializer, ActiveMixin
from ..user.serializers import EditorBaseSerializer
from .models import Tutorial, AboutUs, Banner, Privacy


class IndexBannerSerializer(ProductListSerializer):
    imgUrl = serializers.SerializerMethodField()

    class Meta:
        model = Banner
        fields = ('id', 'title', 'detail', 'imgUrl', 'link')

    def get_imgUrl(self, instance):
        return "{}/{}".format(settings.IMAGE_ROOT, instance.image) if instance.image else None


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


class PrivacySerializer(serializers.ModelSerializer):
    class Meta:
        model = Privacy
        fields = ('detail',)


class AdminPrivacySerializer(EditorBaseSerializer):
    class Meta:
        model = Privacy
        fields = ('detail', "createTime", "updateTime", "creator", "updater")


class TutorialSerializer(serializers.ModelSerializer):
    imgUrl = serializers.SerializerMethodField()

    class Meta:
        model = Tutorial
        fields = ('id', 'title', 'description', 'imgUrl', 'link')

    def get_imgUrl(self, instance):
        return "{}/{}".format(settings.IMAGE_ROOT, instance.image) if instance.image else None


class TutorialLinkSerializer(TutorialSerializer):
    class Meta:
        model = Tutorial
        fields = ('id', 'title', 'link', 'imgUrl')


class AdminTutorialCreateSerializer(TutorialSerializer, EditorBaseSerializer):
    file = serializers.ImageField(write_only=True, source="image")

    class Meta:
        model = Tutorial
        fields = ('id', 'title', 'file', 'link', 'imgUrl',
                  "createTime", "updateTime", "creator", "updater")


class AdminBannerSerializer(IndexBannerSerializer, EditorBaseSerializer, ActiveMixin):

    class Meta:
        model = Banner
        fields = ('id', 'title', 'detail', 'imgUrl', 'link',
                  "createTime", "updateTime", "creator", "updater",
                  'isActive', 'activeTime', 'inactiveTime')


class AdminBannerCreateSerializer(AdminBannerSerializer):
    file = serializers.ImageField(write_only=True, source="image")

    class Meta:
        model = Banner
        fields = ('id', 'title', 'detail', 'file', 'link', 'imgUrl',
                  "createTime", "updateTime", "creator", "updater",
                  'isActive', 'activeTime', 'inactiveTime')


class AdminBannerActiveSerializer(AdminBannerSerializer):

    class Meta:
        model = Banner
        fields = ('id', 'title', 'detail', 'link', 'imgUrl',
                  "createTime", "updateTime", "creator", "updater",
                  'isActive', 'activeTime', 'inactiveTime')
        read_only_fields = ('id', 'title', 'detail', 'link', 'imgUrl',
                            "createTime", "updateTime", "creator", "updater",
                            'activeTime', 'inactiveTime')
