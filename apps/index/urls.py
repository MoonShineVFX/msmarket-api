from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^common$', views.CommonView.as_view(), name='common'),
    url(r'^index$', views.IndexView.as_view(), name='index'),
    url(r'^about_us$', views.AboutUsView.as_view(), name='about_us'),
    url(r'^tutorials$', views.TutorialListView.as_view(), name='tutorial_list'),
]