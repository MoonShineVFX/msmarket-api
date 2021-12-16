from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^order_create$', views.OrderCreate.as_view(), name='order_create'),
    url(r'^newebpay_payment_notify$', views.NewebpayPaymentNotify.as_view(), name='newebpay-payment-notify'),

    url(r'^cart_products$', views.CartProductList.as_view(), name='cart_product_list'),
    url(r'^cart_product_add$', views.CartProductAdd.as_view(), name='cart_product_add'),
    url(r'^cart_product_remove$', views.CartProductRemove.as_view(), name='cart_product_remove'),
]