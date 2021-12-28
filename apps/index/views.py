from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Banner, Tutorial
from ..product.models import Product
from ..category.models import Tag

from ..category.serializers import TagNameOnlySerializer
from ..product.serializers import WebProductListSerializer
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


class IndexView(APIView):
    def post(self, request):
        banner_products = [banner.product for banner in Banner.objects.select_related("product").all()]
        new_products = Product.objects.order_by("-id")[:4]
        tutorials = Tutorial.objects.order_by("-id")[:3]

        data = {
            "banners": serializers.BannerProductSerializer(banner_products, many=True).data,
            "newArrivals": WebProductListSerializer(new_products, many=True).data,
            "tutorials": serializers.TutorialSerializer(tutorials, many=True).data,
        }

        return Response(data, status=status.HTTP_200_OK)