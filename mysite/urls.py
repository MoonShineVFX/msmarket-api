from django.conf.urls import url, include

urlpatterns = [
    url(r'^api/', include('apps.category.urls')),
    url(r'^api/', include('apps.product.urls')),
    url(r'^api/', include('apps.order.urls')),
    url(r'^api/', include('apps.user.urls')),
    url(r'^api/', include('apps.index.urls')),
    #url(r'accounts/', include('allauth.urls')),  # django-allauth網址
]
