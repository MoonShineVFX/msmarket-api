from django.db.models import Prefetch
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from ..shortcuts import WebCreateView, PostUpdateView
from .models import Product, Model
from ..order.models import Order
from ..category.models import category, category_key_2_id
from . import serializers
from ..pagination import ProductPagination
from rest_framework.permissions import IsAuthenticated, IsAdminUser


class ProductList(ListAPIView):
    pagination_class = ProductPagination
    serializer_class = serializers.ProductListSerializer
    queryset = Product.objects.prefetch_related('tags').all()

    def filter_queryset(self, queryset):
        category_key = self.request.query_params.get('type', 'all')
        if category_key != "all" and category_key in category:
            queryset = queryset.filter(status=category_key_2_id.get(category_key))

        tag_ids = self.request.query_params.get('tags', None)
        if tag_ids:
            tag_list = tag_ids.split(",")
            for tag in tag_list:
                queryset = queryset.filter(tags__id=tag)
        return queryset


class ProductDetail(RetrieveAPIView):
    serializer_class = serializers.ProductDetailSerializer
    models = Model.objects.select_related("format", "renderer")
    queryset = Product.objects.prefetch_related("tags", "images").prefetch_related(Prefetch('models', queryset=models))


class MyProductList(ListAPIView):
    serializer_class = serializers.MyProductSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            paid_orders = Order.objects.filter(user_id=self.request.user.id, status=Order.SUCCESS)
            models = Model.objects.select_related("format", "renderer")
            return Product.objects.prefetch_related(
                Prefetch('models', queryset=models)).filter(orders__in=paid_orders).distinct()
        return Product.objects.none()


class AdminProductList(ListAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminProductListSerializer
    queryset = Product.objects.select_related(
        "creator", "updater").prefetch_related('tags').order_by(
        "active_at", "inactive_at", "updated_at", "created_at")


class AdminProductSearch(AdminProductList):
    def filter_queryset(self, queryset):
        query = self.request.data.get('query', None)
        if query:
            queryset = queryset.filter(title__icontains=query)
        return queryset


class AdminProductDetail(RetrieveAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminProductDetailSerializer
    queryset = Product.objects.select_related(
        "main_image", "mobile_main_image", "thumb_image", "extend_image",
        "creator", "updater").prefetch_related("tags", "images")


class AdminProductCreate(WebCreateView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminProductCreateSerializer


class AdminProductUpdate(PostUpdateView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminProductCreateSerializer
    queryset = Product