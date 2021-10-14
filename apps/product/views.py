from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from .models import Product


class ProductList(ListAPIView):
    queryset = Product.objects.all()


class ProductDetail(RetrieveAPIView):
    queryset = Product.objects.all()