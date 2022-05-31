from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^order_create$', views.OrderCreate.as_view(), name='order_create'),
    url(r'^newebpay_from_order$', views.GetNewebpayDataFromOrder.as_view(), name='newebpay-from-order'),

    url(r'^orders$', views.OrderList.as_view(), name='order_list'),
    url(r'^orders/(?P<order_number>[0-9A-Za-z\-]+)$', views.OrderDetail.as_view(), name='order_detail'),

    url(r'^admin_orders$', views.AdminOrderList.as_view(), name='admin_order_list'),
    url(r'^admin_order_search$', views.AdminOrderSearch.as_view(), name='admin_order_search'),
    url(r'^admin_orders/(?P<order_number>[0-9A-Za-z\-]+)$', views.AdminOrderDetail.as_view(), name='admin_order_detail'),

    url(r'^newebpay_payment_notify$', views.NewebpayPaymentNotify.as_view(), name='newebpay-payment-notify'),

    url(r'^cart_products$', views.CartProductList.as_view(), name='cart_product_list'),
    url(r'^cart_product_add$', views.CartProductAdd.as_view(), name='cart_product_add'),
    url(r'^cart_product_remove$', views.CartProductRemove.as_view(), name='cart_product_remove'),

    url(r'^admin_e_invoice_create$', views.CreateEZPayInvoiceFromOrder.as_view(), name='admin-e-invoice-create'),
    url(r'^admin_order_paper_invoice_create$', views.AdminOrderPaperInvoiceUpdate.as_view(),
        name='admin-order-paper-invoice-create'),
    url(r'^admin_order_paper_invoice_update$', views.AdminOrderPaperInvoiceUpdate.as_view(),
        name='admin-order-paper-invoice-update'),
]
