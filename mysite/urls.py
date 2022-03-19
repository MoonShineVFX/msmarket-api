from django.conf.urls import url, include
from django.contrib import admin
urlpatterns = [
    url(r'^api/', include('apps.category.urls')),
    url(r'^api/', include('apps.product.urls')),
    url(r'^api/', include('apps.order.urls')),
    url(r'^api/', include('apps.user.urls')),
    url(r'^api/', include('apps.index.urls')),
    url(r'^api/', include('apps.lang.urls')),
]
