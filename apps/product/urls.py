from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^products$', views.ProductList.as_view(), name='product-list'),
    url(r'^products/(?P<pk>\d+)$', views.ProductDetail.as_view(), name='product-detail'),

    url(r'^my_products$', views.MyProductList.as_view(), name='my_product_list'),

    url(r'^admin_products$', views.AdminProductList.as_view(), name='admin-product-list'),
    url(r'^admin_products/(?P<pk>\d+)$', views.AdminProductDetail.as_view(), name='admin-product-detail'),
]