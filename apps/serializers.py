# -*- coding: utf-8 -*-
from rest_framework import serializers


class EditorBaseSerializer(serializers.ModelSerializer):
    createTime = serializers.SerializerMethodField()
    updateTime = serializers.SerializerMethodField()
    creator = serializers.SerializerMethodField()
    updater = serializers.SerializerMethodField()

    def get_createTime(self, instance):
        return instance.created_at if instance.created_at else ""

    def get_updateTime(self, instance):
        return instance.updated_at if instance.updated_at else ""

    def get_creator(self, instance):
        return instance.creator.username if instance.creator else ""

    def get_updater(self, instance):
        return instance.updater.username if instance.updater else ""