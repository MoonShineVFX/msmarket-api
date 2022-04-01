from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from ..authentications import AdminJWTAuthentication

from .models import LangConfig
from . import serializers

from rest_framework.response import Response
from rest_framework import status


class LangConfigListView(APIView):
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        lang_configs = LangConfig.objects.all()
        data = dict()
        updated_at = None
        for lang in lang_configs:
            data[lang.lang] = serializers.LangConfigSerializer(lang).data

            if not updated_at:
                updated_at = lang.updated_at
            elif lang.updated_at > updated_at:
                updated_at = lang.updated_at
        data["updatedAt"] = updated_at
        return Response(data, status=status.HTTP_200_OK)


class AdminLangConfigSearchView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)

    def post(self, request, *args, **kwargs):
        query_key = request.data.get('key', None)
        query_value = request.data.get('value', None)

        lang_configs = LangConfig.objects.all()
        data = dict()
        lang_code = list()
        all_fields = [key for key, value in serializers.LangConfigSerializer().fields.items()]

        if query_key:
            result_fields = [key for key in all_fields if query_key.lower() in key.lower()]
        else:
            result_fields = all_fields

        for lang_config in lang_configs:
            lang_code.append(lang_config.lang)
            data[lang_config.lang] = serializers.LangConfigSearchSerializer(lang_config, fields=result_fields).data

        if query_value:
            contain_value_fields = list()

            for lang_key in lang_code:
                for field in result_fields:
                    if data[lang_key][field] and query_value.lower() in data[lang_key][field].lower():
                        contain_value_fields.append(field)

            for lang_config in lang_configs:
                data[lang_config.lang] = serializers.LangConfigSearchSerializer(lang_config, fields=contain_value_fields).data

        return Response(data, status=status.HTTP_200_OK)


class AdminLangConfigUpdateView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)

    def post(self, request, *args, **kwargs):
        for lang in request.data:
            serializer = serializers.LangConfigSerializer(data=request.data[lang])
            serializer.is_valid()
            update_data = {"updated_at": timezone.now()}
            update_data.update(serializer.validated_data)
            LangConfig.objects.filter(lang=lang).update(**update_data)
        return Response(request.data, status=status.HTTP_200_OK)
