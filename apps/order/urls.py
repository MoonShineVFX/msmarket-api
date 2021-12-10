from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^web_order_create$', views.OrderCreate.as_view(), name='order_create'),
    # url(r'^newebpay_payment_notify$', views.WebProductDetail.as_view(), name='newebpay-payment-notify'),
]