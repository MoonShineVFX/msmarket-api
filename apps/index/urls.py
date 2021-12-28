from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^common$', views.CommonView.as_view(), name='common'),
    url(r'^index$', views.IndexView.as_view(), name='index'),
]