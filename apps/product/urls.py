from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^products$', views.ProductList.as_view(), name='web-product-list'),
    url(r'^products/(?P<pk>\d+)$', views.ProductDetail.as_view(), name='web-product-detail'),

    url(r'^my_products$', views.MyProductList.as_view(), name='my_product_list'),
]