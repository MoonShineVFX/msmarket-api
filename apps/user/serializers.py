# -*- coding: utf-8 -*-
from django.db.models import Q
from django.conf import settings
from ..serializers import EditorBaseSerializer
from rest_framework import serializers
from .models import User, AdminProfile


class RegisterCustomerSerializer(serializers.Serializer):
    realName = serializers.CharField(required=False)
    nickname = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField()

    def create(self, validated_data):
        name = validated_data.pop('realName', None)
        nick_name = validated_data.pop('nickname')
        email = validated_data.pop('email')
        password = validated_data.pop('password')

        user = User.objects.create(name=name, nick_name=nick_name, email=email)
        user.set_password(raw_password=password)
        user.save()
        return user


class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.CharField(required=False)


class AdminUserSerializer(EditorBaseSerializer):
    isAssetAdmin = serializers.BooleanField(source="is_asset_admin")
    isFinanceAdmin = serializers.BooleanField(source="is_finance_admin")
    isSuperuser = serializers.BooleanField(source="is_superuser")

    class Meta:
        model = User
        fields = ('id', 'email', 'isAssetAdmin', 'isFinanceAdmin', 'isSuperuser',
                  "createTime", "updateTime")

    def get_isAssetAdmin(self, instance):
        return instance.is_asset_admin

    def get_isFinanceAdmin(self, instance):
        return instance.is_finance_admin


class AdminUserCreateSerializer(AdminUserSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'isAssetAdmin', 'isFinanceAdmin', 'isSuperuser',
                  "createTime", "updateTime")
        read_only_fields = ['id', "createTime", "updateTime"]

    def create(self, validated_data):
        is_asset_admin = validated_data.pop('is_asset_admin', False)
        is_finance_admin = validated_data.pop('is_finance_admin', False)
        password = validated_data.pop("password")
        validated_data["is_staff"] = True

        user = User(**validated_data)
        user.set_password(raw_password=password)
        user.save()
        AdminProfile.objects.create(user=user, is_asset_admin=is_asset_admin, is_finance_admin=is_finance_admin)
        return user


class AdminUserUpdateSerializer(AdminUserSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'isAssetAdmin', 'isFinanceAdmin', 'isSuperuser',
                      "createTime", "updateTime")
        read_only_fields = ['id', 'email', "createTime", "updateTime"]

    def update(self, instance, validated_data):
        is_asset_admin = validated_data.pop('is_asset_admin', False)
        is_finance_admin = validated_data.pop('is_finance_admin', False)

        instance.admin_profile.is_asset_admin = is_asset_admin
        instance.admin_profile.is_finance_admin = is_finance_admin
        instance.admin_profile.save()

        return super().update(instance, validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField()
    newPassword = serializers.CharField()