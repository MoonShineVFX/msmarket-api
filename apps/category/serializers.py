# -*- coding: utf-8 -*-
import datetime
from rest_framework import serializers
from ..serializers import EditorBaseSerializer
from .models import Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class TagNameOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name')


class AdminTagSerializer(EditorBaseSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "createTime", "updateTime", "creator", "updater")


class TagListCreateSerializer(serializers.Serializer):
    tags = serializers.ListSerializer(child=TagNameOnlySerializer())

    def create(self, validated_data):
        tags = [
            Tag(name=tag['name'], creator_id=validated_data["creator_id"])
            for tag in validated_data['tags']]
        created_tags = Tag.objects.bulk_create(tags)
        return created_tags[0]


class TagUpdateSerializer(EditorBaseSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'createTime', 'updateTime', 'creator', 'updater')

