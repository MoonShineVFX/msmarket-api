# -*- coding: utf-8 -*-
from rest_framework import serializers
from django.conf import settings
from ..product.serializers import WebProductListSerializer
from .models import Product, Tutorial, AboutUs


class BannerProductSerializer(WebProductListSerializer):
    class Meta:
        model = Product
        fields = ('id', 'title', 'description', 'imgUrl', 'price', 'status')


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

