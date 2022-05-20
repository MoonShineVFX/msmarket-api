from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^products$', views.ProductList.as_view(), name='product-list'),
    url(r'^products/(?P<pk>\d+)$', views.ProductDetail.as_view(), name='product-detail'),
    url(r'^product_xltn$', views.ProductXLTNView.as_view(), name='product-xltn'),

    url(r'^my_products$', views.MyProductList.as_view(), name='my-product-list'),

    url(r'^admin_products$', views.AdminProductList.as_view(), name='admin-product-list'),
    url(r'^admin_product_search$', views.AdminProductSearch.as_view(), name='admin-product-search'),
    url(r'^admin_products/(?P<pk>\d+)$', views.AdminProductDetail.as_view(), name='admin-product-detail'),
    url(r'^admin_product_create$', views.AdminProductCreate.as_view(), name='admin-product-create'),
    url(r'^admin_product_update$', views.AdminProductUpdate.as_view(), name='admin-product-update'),
    url(r'^admin_product_active$', views.AdminProductActive.as_view(), name='admin-product-active'),

    url(r'^admin_image_upload$', views.AdminImageUpload.as_view(), name='admin-image-upload'),
    url(r'^admin_image_delete$', views.AdminImageDelete.as_view(), name='admin-image-delete'),

    url(r'^admin_model_upload_uri$', views.AdminModelUploadUrI.as_view(), name='admin-model-upload-uri'),

    url(r'^model_download_link$', views.ModelDownloadLink.as_view(), name='model-download-link'),
]

