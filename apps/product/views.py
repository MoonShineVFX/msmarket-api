from django.db.models import Prefetch
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from .models import Product, Model
from ..category.models import category, category_key_2_id
from . import serializers
from ..pagination import ProductPagination


class WebProductList(ListAPIView):
    pagination_class = ProductPagination
    serializer_class = serializers.WebProductListSerializer
    queryset = Product.objects.prefetch_related('tags').all()

    def filter_queryset(self, queryset):
        category_key = self.request.query_params.get('type', 'all')
        if category_key != "all":
            queryset = queryset.filter(status=category_key_2_id[category_key])

        tag_ids = self.request.query_params.get('tags', None)
        if tag_ids:
            tag_list = tag_ids.split(",")
            for tag in tag_list:
                queryset = queryset.filter(tags__id=tag)
        return queryset


class WebProductDetail(RetrieveAPIView):
    serializer_class = serializers.WebProductDetailSerializer
    models = Model.objects.select_related("format", "renderer")
    queryset = Product.objects.prefetch_related("tags", "images").prefetch_related(Prefetch('models', queryset=models))


class MyProductList(ListAPIView):
    serializer_class = serializers.WebProductDetailSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Product.objects.prefetch_related("models").filter(user_id=self.request.user.id)
        return Product.objects.none()