import requests
from django.conf import settings
from django.utils import timezone
from django.db.models import Prefetch
from rest_framework.generics import ListAPIView, RetrieveAPIView, GenericAPIView
from ..shortcuts import (
    WebCreateView, PostCreateView, PostUpdateView, PostListView, PostDestroyView,
    CreateActiveViewMixin, UpdateActiveViewMixin, BaseXLTNView,
    RetrieveSwitchLangMixin, ListSwitchLangMixin
)
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from ..storage import generate_signed_url_v2, generate_session_uri_for_upload

from .models import Product, Model, Image, Format, Renderer
from ..user.models import CustomerProduct
from . import serializers
from ..pagination import ProductPagination
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from ..authentications import AdminJWTAuthentication, CustomerJWTAuthentication


class ProductList(ListSwitchLangMixin, ListAPIView):
    pagination_class = ProductPagination
    serializer_class = serializers.ProductListSerializer
    queryset = Product.objects.prefetch_related('tags').filter(is_active=True).order_by('-active_at')

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


class ProductDetail(RetrieveSwitchLangMixin, RetrieveAPIView):
    serializer_class = serializers.ProductDetailSerializer
    models = Model.objects.select_related("format", "renderer")
    queryset = Product.objects.prefetch_related("tags", "images").prefetch_related(Prefetch('models', queryset=models))


class ProductXLTNView(BaseXLTNView):
    serializer_class = serializers.ProductXLTNSerializer
    queryset = Product.objects.all()


class MyProductList(PostListView):
    authentication_classes = [CustomerJWTAuthentication]
    serializer_class = serializers.MyProductSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            bought_products = CustomerProduct.objects.values_list("product_id", flat=True).filter(user_id=self.request.user.id)
            models = Model.objects.select_related("format", "renderer")
            return Product.objects.prefetch_related(
                Prefetch('models', queryset=models)).filter(id__in=bought_products)
        return Product.objects.none()


class AdminProductList(PostListView):
    authentication_classes = [AdminJWTAuthentication]
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
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminProductDetailSerializer
    queryset = Product.objects.select_related(
        "main_image", "mobile_main_image", "thumb_image", "extend_image",
        "creator", "updater").prefetch_related("tags", "images", "models")

    def post(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class AdminProductCreate(CreateActiveViewMixin, WebCreateView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminProductCreateSerializer


class AdminProductUpdate(UpdateActiveViewMixin, PostUpdateView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminProductCreateSerializer
    translation_serializer_class = serializers.ProductXLTNSerializer
    queryset = Product


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
    authentication_classes = [AdminJWTAuthentication]
    serializer_class = serializers.ImageUploadSerializer
    queryset = Image.objects.all()


class AdminPreviewImageListUpload(GenericAPIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.PreviewListUploadSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=self.request.data)
        if serializer.is_valid():
            image = serializer.save(**{"creator_id": self.request.user.id})
            previews = Image.objects.filter(product_id=image.product_id, position_id=Image.PREVIEW).all()
            dump_serializer = serializers.WebImageSerializer(previews, many=True)
            return Response({"list": dump_serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminImageDelete(PostDestroyView):
    authentication_classes = [AdminJWTAuthentication]
    queryset = Image.objects.all()


class ModelDownloadLink(GenericAPIView):
    authentication_classes = [CustomerJWTAuthentication]
    permission_classes = (IsAuthenticated, )

    def user_has_product(self, user_id, product_id):
        return Product.objects.filter(orders__user_id=user_id, id=product_id).exists()

    def post(self, request, *args, **kwargs):
        product_id = self.request.data.get('productId', None)
        format_id = self.request.data.get('formatId', None)
        renderer_id = self.request.data.get('rendererId', None)
        if self.user_has_product(user_id=self.request.user.id, product_id=product_id):
            model = get_object_or_404(Model, product_id=product_id, format_id=format_id, renderer_id=renderer_id)
            url = generate_signed_url_v2(file_path=model.file)
            return Response(data={"url": url}, status=status.HTTP_200_OK)
        return Response(data="User hasn't buy the product", status=status.HTTP_403_FORBIDDEN)


class AdminModelUploadUrI(GenericAPIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        serializer = serializers.CreateModelSerializer(data=request.data)
        if serializer.is_valid():
            model = serializer.save(**{"creator_id": self.request.user.id})
            session_uri = generate_session_uri_for_upload(file_path=model.file)

            if session_uri:
                return Response(data={"sessionUri": session_uri}, status=status.HTTP_200_OK)
            else:
                return Response("session_uri is empty", status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminProductModelList(GenericAPIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)

    def get(self, request, pk, *args, **kwargs):
        product = get_object_or_404(Product.objects.only("title"), pk=pk)
        models = Model.objects.filter(product_id=pk).select_related("creator").all()
        formats = Format.objects.all()
        renderers = Renderer.objects.all()

        data = {
            "title": product.title,
            "models": serializers.AdminModelSerializer(models, many=True).data,
            "formats": serializers.FormatSerializer(formats, many=True).data,
            "renderers": serializers.FormatSerializer(renderers, many=True).data
        }
        return Response(data=data, status=status.HTTP_200_OK)

