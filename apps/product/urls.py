from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^products$', views.ProductList.as_view(), name='product-list'),
    url(r'^products/(?P<pk>\d+)$', views.ProductDetail.as_view(), name='product-detail'),
]