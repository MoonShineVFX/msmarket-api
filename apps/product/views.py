from django.utils import timezone
from django.db.models import Prefetch
from rest_framework.generics import ListAPIView, RetrieveAPIView, GenericAPIView
from ..shortcuts import WebCreateView, PostCreateView, PostUpdateView, PostListView, PostDestroyView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from ..storage import get_download_link

from .models import Product, Model, Image
from ..order.models import Order
from . import serializers
from ..pagination import ProductPagination
from rest_framework.permissions import IsAuthenticated, IsAdminUser


class ProductList(ListAPIView):
    pagination_class = ProductPagination
    serializer_class = serializers.ProductListSerializer
    queryset = Product.objects.prefetch_related('tags').filter(is_active=True)

    def filter_queryset(self, queryset):
        """
        category_key = self.request.query_params.get('type', 'all')
        if category_key != "all" and category_key in category:
            queryset = queryset.filter(category=category_key_2_id.get(category_key))

        """
        tag_ids = self.request.query_params.get('tags', None)
        if tag_ids:
            tag_list = tag_ids.split(",")
            for tag in tag_list:
                queryset = queryset.filter(tags__id=tag)
        return queryset


class ProductDetail(RetrieveAPIView):
    serializer_class = serializers.ProductDetailSerializer
    models = Model.objects.select_related("format", "renderer")
    queryset = Product.objects.prefetch_related("tags", "images").prefetch_related(Prefetch('models', queryset=models)).filter(is_active=True)


class MyProductList(PostListView):
    serializer_class = serializers.MyProductSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            paid_orders = Order.objects.filter(user_id=self.request.user.id, status=Order.SUCCESS)
            models = Model.objects.select_related("format", "renderer")
            return Product.objects.prefetch_related(
                Prefetch('models', queryset=models)).filter(orders__in=paid_orders).distinct()
        return Product.objects.none()


class AdminProductList(PostListView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminProductListSerializer
    queryset = Product.objects.select_related(
        "creator", "updater").prefetch_related('tags').order_by(
        "-active_at", "-inactive_at", "-updated_at", "-created_at")


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

    def post(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class AdminProductCreate(WebCreateView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminProductCreateSerializer


class AdminProductUpdate(PostUpdateView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminProductCreateSerializer
    queryset = Product

    def perform_update(self, serializer):
        data = {"updater_id": self.request.user.id, "updated_at": timezone.now()}

        is_active = serializer.validated_data.get("is_active", None)
        if is_active is not None:
            if is_active:
                data.update({"active_at": timezone.now()})
            else:
                data.update({"inactive_at": timezone.now()})

        serializer.save(**data)


class AdminProductActive(AdminProductUpdate):
    serializer_class = serializers.AdminProductActiveSerializer
    queryset = Product.objects.select_related("creator", "updater")

    def perform_update(self, serializer):
        is_active = serializer.validated_data.get("is_active")
        data = {"updater_id": self.request.user.id, "updated_at": timezone.now(), "is_active": is_active}

        if is_active:
            data.update({"active_at": timezone.now()})
        else:
            data.update({"inactive_at": timezone.now()})

        Product.objects.filter(id=serializer.instance.id).update(**data)


class AdminImageUpload(PostCreateView):
    serializer_class = serializers.UploadImageSerializer
    queryset = Image.objects.all()


class AdminImageDelete(PostDestroyView):
    queryset = Image.objects.all()


class ModelDownloadLink(GenericAPIView):
    permission_classes = (IsAuthenticated, )

    def user_has_product(self, user_id, product_id):
        return Product.objects.filter(orders__user_id=user_id, id=product_id).exists()

    def post(self, request, *args, **kwargs):
        product_id = self.request.data.get('productId', None)
        format_id = self.request.data.get('formatId', None)
        render_id = self.request.data.get('renderId', None)
        if self.user_has_product(user_id=self.request.user.id, product_id=product_id):
            model = get_object_or_404(Model, id=product_id, format_id=format_id, render_id=render_id)
            url = get_download_link(file_path=model.file)
            return Response(data={"url": url}, status=status.HTTP_200_OK)
        return Response(data="User hasn't buy the product", status=status.HTTP_403_FORBIDDEN)

