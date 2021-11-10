from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^web_products$', views.WebProductList.as_view(), name='web-product-list'),
    url(r'^web_products/(?P<pk>\d+)$', views.WebProductDetail.as_view(), name='web-product-detail'),
]