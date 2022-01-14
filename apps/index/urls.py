from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^common$', views.CommonView.as_view(), name='common'),
    url(r'^index$', views.IndexView.as_view(), name='index'),
    url(r'^about_us$', views.AboutUsView.as_view(), name='about-us'),
    url(r'^tutorials$', views.TutorialListView.as_view(), name='tutorial-list'),

    url(r'^admin_common$', views.AdminCommonView.as_view(), name='admin-common'),
    url(r'^admin_about$', views.AdminAboutUsView.as_view(), name='admin-about'),
    url(r'^admin_about_update$', views.AdminAboutUsUpdate.as_view(), name='admin-about-update'),
]