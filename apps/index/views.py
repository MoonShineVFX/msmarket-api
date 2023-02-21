from django.utils import timezone
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from ..shortcuts import (
    PostListView, PostCreateView, PostUpdateView, CreateActiveViewMixin, UpdateActiveViewMixin, BaseXLTNView,
    ListSwitchLangMixin, RetrieveSwitchLangMixin, SwitchLangMixin
)
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from ..authentications import AdminJWTAuthentication, CustomerJWTAuthentication

from .models import Banner, Tutorial, AboutUs, Privacy
from ..product.models import Product, Image
from ..order.models import Currency
from ..category.models import Tag
from ..lang.models import LangConfig

from ..user.serializers import CommonCustomerSerializer
from ..category.serializers import TagNameOnlySerializer
from ..product.serializers import ProductListSerializer, ImagePositionTypeSerializer
from . import serializers

from django.utils.translation import get_language, activate


class SetLanguageView(APIView):
    def post(self, request):
        lang_code = request.data.get('langCode', None)
        response = Response(status=status.HTTP_200_OK)
        if lang_code and lang_code in settings.MODELTRANSLATION_LANGUAGES:
            response.set_cookie(key="django_language", value=lang_code, httponly=True, secure=True, samesite="Strict")
        return response


class CommonView(APIView, SwitchLangMixin):
    authentication_classes = [CustomerJWTAuthentication]

    def post(self, request):
        self.set_language()
        tags = Tag.objects.all()
        lang_config = LangConfig.objects.only('updated_at').latest('updated_at')
        usd_currency = Currency.objects.first()
        fx_rate = usd_currency.currency if usd_currency else 1
        data = {
            "tags": TagNameOnlySerializer(tags, many=True).data,
            "langConfigUpdatedAt": lang_config.updated_at,
            "fxRate": fx_rate
        }
        data.update(CommonCustomerSerializer(request.user).data)
        return Response(data, status=status.HTTP_200_OK)


class AdminCommonView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)

    def post(self, request):
        tags = Tag.objects.all()

        data = {
            "userId": request.user.id if request.user.is_authenticated else None,
            "account": request.user.email if request.user.is_authenticated else None,
            "tags": TagNameOnlySerializer(tags, many=True).data,
            "imagePosition": ImagePositionTypeSerializer(Image.position_types, many=True).data
        }

        return Response(data, status=status.HTTP_200_OK)


class IndexView(APIView, SwitchLangMixin):
    def post(self, request):
        self.set_language()
        banners = Banner.objects.filter(is_active=True).all()
        new_products = Product.objects.filter(is_active=True).order_by("-active_at")[:4]
        tutorials = Tutorial.objects.filter(is_active=True).order_by("-created_at")[:3]

        data = {
            "banners": serializers.IndexBannerSerializer(banners, many=True).data,
            "products": ProductListSerializer(new_products, many=True).data,
            "tutorials": serializers.TutorialSerializer(tutorials, many=True).data,
        }

        return Response(data, status=status.HTTP_200_OK)


class AboutUsView(RetrieveSwitchLangMixin, RetrieveAPIView):
    serializer_class = serializers.AboutUsSerializer

    def get_object(self):
        return AboutUs.objects.first()

    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)


class PrivacyView(RetrieveSwitchLangMixin, RetrieveAPIView):
    serializer_class = serializers.PrivacySerializer

    def get_object(self):
        return Privacy.objects.first()

    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)


class TutorialListView(GenericAPIView, SwitchLangMixin):
    serializer_class = serializers.TutorialLinkSerializer
    queryset = Tutorial.objects.filter(is_active=True).order_by('-created_at')

    def post(self, request, *args, **kwargs):
        self.set_language()
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = {
            "list": serializer.data,
        }
        return Response(data, status=status.HTTP_200_OK)


class AboutUsXLTNView(BaseXLTNView):
    serializer_class = serializers.AboutUsXLTNSerializer

    def get_object(self):
        return AboutUs.objects.first()


class PrivacyXLTNView(BaseXLTNView):
    serializer_class = serializers.PrivacyXLTNSerializer

    def get_object(self):
        return Privacy.objects.first()


class TutorialXLTNView(BaseXLTNView):
    serializer_class = serializers.TutorialXLTNSerializer
    queryset = Tutorial.objects.all()


class BannerXLTNView(BaseXLTNView):
    serializer_class = serializers.BannerXLTNSerializer
    queryset = Banner.objects.all()


class AdminAboutUsView(RetrieveAPIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminAboutUsSerializer

    def get_object(self):
        return AboutUs.objects.select_related("creator", "updater").first()

    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)


class AdminAboutUsUpdate(PostUpdateView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminAboutUsSerializer
    translation_serializer_class = serializers.AboutUsXLTNSerializer

    def get_object(self):
        return AboutUs.objects.select_related("creator", "updater").first()


class AdminPrivacyView(RetrieveAPIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminPrivacySerializer

    def get_object(self):
        return Privacy.objects.select_related("creator", "updater").first()

    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)


class AdminPrivacyUpdate(PostUpdateView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminPrivacySerializer
    translation_serializer_class = serializers.PrivacyXLTNSerializer

    def get_object(self):
        return Privacy.objects.select_related("creator", "updater").first()


class AdminTutorialListView(PostListView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminTutorialCreateSerializer
    queryset = Tutorial.objects.select_related("creator", "updater").order_by("-updated_at","-created_at")


class AdminTutorialCreateView(PostCreateView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminTutorialCreateSerializer


class AdminTutorialUpdateView(PostUpdateView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminTutorialCreateSerializer
    queryset = Tutorial.objects.select_related("creator", "updater")
    translation_serializer_class = serializers.TutorialXLTNSerializer


class AdminTutorialActiveView(PostUpdateView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminTutorialActiveSerializer
    queryset = Tutorial.objects.select_related("creator", "updater")

    def perform_update(self, serializer):
        is_active = serializer.validated_data.get("is_active")
        data = {"updater_id": self.request.user.id, "updated_at": timezone.now(), "is_active": is_active}

        if is_active:
            data.update({"active_at": timezone.now()})
        else:
            data.update({"inactive_at": timezone.now()})
        Tutorial.objects.filter(id=serializer.instance.id).update(**data)
        for key, value in data.items():
            setattr(serializer.instance, key, value)
        
        
class AdminBannerListView(PostListView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminBannerSerializer
    queryset = Banner.objects.select_related("creator", "updater")


class AdminBannerCreateView(CreateActiveViewMixin, PostCreateView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminBannerCreateSerializer


class AdminBannerUpdateView(UpdateActiveViewMixin, PostUpdateView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminBannerCreateSerializer
    queryset = Banner.objects.select_related("creator", "updater")
    translation_serializer_class = serializers.BannerXLTNSerializer


class AdminBannerActiveView(PostUpdateView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminBannerCreateSerializer
    queryset = Banner.objects.select_related("creator", "updater")

    def perform_update(self, serializer):
        is_active = serializer.validated_data.get("is_active")
        data = {"updater_id": self.request.user.id, "updated_at": timezone.now(), "is_active": is_active}

        if is_active:
            data.update({"active_at": timezone.now()})
        else:
            data.update({"inactive_at": timezone.now()})

        Banner.objects.filter(id=serializer.instance.id).update(**data)
        for key, value in data.items():
            setattr(serializer.instance, key, value)