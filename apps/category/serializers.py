# -*- coding: utf-8 -*-
import datetime
from rest_framework import serializers
from .models import Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class TagNameOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name')
