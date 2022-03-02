# -*- coding: utf-8 -*-
from django.db.models import Q
from django.conf import settings
from rest_framework.serializers import ValidationError
from ..serializers import EditorBaseSerializer
from rest_framework import serializers
from .models import User, AdminProfile


class RegisterCustomerSerializer(serializers.Serializer):
    realName = serializers.CharField(required=False)
    nickname = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate_email(self, data):
        if User.objects.filter(email=data).exists():
            raise ValidationError("Email already exists")
        return data

    def create(self, validated_data):
        name = validated_data.pop('realName', None)
        nick_name = validated_data.pop('nickname')
        email = validated_data.pop('email')
        password = validated_data.pop('password')

        user = User.objects.create(name=name, nick_name=nick_name, email=email)
        user.set_password(raw_password=password)
        user.save(update_fields=['password'])
        return user


class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.CharField(required=False)


class ResetPasswordSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField()


class CustomerSerializer(serializers.ModelSerializer):
    nickname = serializers.CharField(source="nick_name")

    class Meta:
        model = User
        fields = ('nickname', 'email')
        read_only_fields = ['email']


class AdminEditorSerializer(serializers.ModelSerializer):
    createTime = serializers.SerializerMethodField()
    updateTime = serializers.SerializerMethodField()
    creator = serializers.SerializerMethodField()
    updater = serializers.SerializerMethodField()

    def get_createTime(self, instance):
        return instance.admin_profile.created_at if instance.admin_profile else ""

    def get_updateTime(self, instance):
        return instance.admin_profile.updated_at if instance.admin_profile else ""

    def get_creator(self, instance):
        return instance.admin_profile.creator.username if instance.admin_profile and instance.admin_profile.creator else ""

    def get_updater(self, instance):
        return instance.admin_profile.updater.username if instance.admin_profile and instance.admin_profile.updater else ""


class AdminUserSerializer(AdminEditorSerializer):
    isAssetAdmin = serializers.BooleanField(source="is_asset_admin")
    isFinanceAdmin = serializers.BooleanField(source="is_finance_admin")
    isSuperuser = serializers.BooleanField(source="is_superuser")

    class Meta:
        model = User
        fields = ('id', 'account', 'isAssetAdmin', 'isFinanceAdmin', 'isSuperuser',
                  "creator", "updater", "createTime", "updateTime")

    def get_isAssetAdmin(self, instance):
        return instance.is_asset_admin

    def get_isFinanceAdmin(self, instance):
        return instance.is_finance_admin


class AdminUserCreateSerializer(AdminUserSerializer):
    password = serializers.CharField(write_only=True)
    account = serializers.CharField(source="email")

    class Meta:
        model = User
        fields = ('id', 'account', 'password', 'isAssetAdmin', 'isFinanceAdmin', 'isSuperuser',
                  "creator", "updater", "createTime", "updateTime")
        read_only_fields = ['id', "createTime", "updateTime"]

    def create(self, validated_data):
        is_asset_admin = validated_data.pop('is_asset_admin', False)
        is_finance_admin = validated_data.pop('is_finance_admin', False)
        creator_id = validated_data.pop('creator_id')
        password = validated_data.pop("password")
        validated_data["is_staff"] = True

        user = User(**validated_data)
        user.set_password(raw_password=password)
        user.save()
        AdminProfile.objects.create(
            user=user, is_asset_admin=is_asset_admin, is_finance_admin=is_finance_admin, creator_id=creator_id)
        return user


class AdminUserUpdateSerializer(AdminUserSerializer):
    class Meta:
        model = User
        fields = ('id', 'account', 'isAssetAdmin', 'isFinanceAdmin', 'isSuperuser',
                      "creator", "updater", "createTime", "updateTime")
        read_only_fields = ['id', 'account']

    def update(self, instance, validated_data):
        is_asset_admin = validated_data.pop('is_asset_admin', False)
        is_finance_admin = validated_data.pop('is_finance_admin', False)
        updater_id = validated_data.pop('updater_id')

        instance.admin_profile.is_asset_admin = is_asset_admin
        instance.admin_profile.is_finance_admin = is_finance_admin
        instance.admin_profile.updater_id = updater_id
        instance.admin_profile.updated_at = validated_data["updated_at"]
        instance.admin_profile.save()

        return super().update(instance, validated_data)


class AdminChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField()
    newPassword = serializers.CharField(source="new_password1")
    confirmNewPassword = serializers.CharField(source="new_password2")