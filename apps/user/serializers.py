# -*- coding: utf-8 -*-
from django.db.models import Q
from django.conf import settings
from rest_framework import serializers
from .models import User


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
