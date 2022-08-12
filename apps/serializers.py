# -*- coding: utf-8 -*-
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken


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


class CreatorBaseSerializer(serializers.ModelSerializer):
    createTime = serializers.SerializerMethodField()
    creator = serializers.SerializerMethodField()

    def get_createTime(self, instance):
        return instance.created_at if instance.created_at else ""

    def get_creator(self, instance):
        return instance.creator.username if instance.creator else ""


class CustomerTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        refresh = RefreshToken.for_user(user)
        refresh['scope'] = "customer"
        return refresh