from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from ..shortcuts import PostListView, PostCreateView, PostUpdateView, PostDestroyView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from .models import Banner, Tutorial, AboutUs
from ..product.models import Product, Image
from ..category.models import Tag

from ..category.serializers import TagNameOnlySerializer
from ..product.serializers import ProductListSerializer, ImagePositionTypeSerializer
from . import serializers


class CommonView(APIView):

    def post(self, request):
        tags = Tag.objects.all()

        data = {
            "userId": request.user.id if request.user.is_authenticated else None,
            "userName": request.user.name if request.user.is_authenticated else None,
            "tags": TagNameOnlySerializer(tags, many=True).data,
        }

        return Response(data, status=status.HTTP_200_OK)


class AdminCommonView(APIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def post(self, request):
        tags = Tag.objects.all()

        data = {
            "userId": request.user.id if request.user.is_authenticated else None,
            "userName": request.user.name if request.user.is_authenticated else None,
            "tags": TagNameOnlySerializer(tags, many=True).data,
            "imagePosition": ImagePositionTypeSerializer(Image.position_types, many=True).data
        }

        return Response(data, status=status.HTTP_200_OK)


class IndexView(APIView):
    def post(self, request):
        banner_products = [banner.product for banner in Banner.objects.select_related("product").all()]
        new_products = Product.objects.order_by("-id")[:4]
        tutorials = Tutorial.objects.order_by("-id")[:3]

        data = {
            "banners": serializers.BannerProductSerializer(banner_products, many=True).data,
            "newArrivals": ProductListSerializer(new_products, many=True).data,
            "tutorials": serializers.TutorialSerializer(tutorials, many=True).data,
        }

        return Response(data, status=status.HTTP_200_OK)


class AboutUsView(RetrieveAPIView):
    serializer_class = serializers.AboutUsSerializer

    def get_object(self):
        return AboutUs.objects.first()

    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)


class TutorialListView(GenericAPIView):
    serializer_class = serializers.TutorialLinkSerializer
    queryset = Tutorial.objects.all()

    def post(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = {
            "list": serializer.data,
        }
        return Response(data, status=status.HTTP_200_OK)


class AdminAboutUsView(RetrieveAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminAboutUsSerializer

    def get_object(self):
        return AboutUs.objects.select_related("creator", "updater").first()

    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)


class AdminAboutUsUpdate(PostUpdateView):
    serializer_class = serializers.AdminAboutUsSerializer

    def get_object(self):
        return AboutUs.objects.select_related("creator", "updater").first()


class AdminTutorialListView(PostListView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminTutorialCreateSerializer
    queryset = Tutorial.objects.select_related("creator", "updater")


class AdminTutorialCreateView(PostCreateView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminTutorialCreateSerializer


class AdminTutorialUpdateView(PostUpdateView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminTutorialCreateSerializer
    queryset = Tutorial.objects.select_related("creator", "updater")
    

class AdminBannerCreateView(PostCreateView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminBannerCreateSerializer


class AdminBannerUpdateView(PostUpdateView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminBannerCreateSerializer
    queryset = Banner.objects.select_related("creator", "updater")