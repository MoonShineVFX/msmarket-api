from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^set_language$', views.SetLanguageView.as_view(), name='set-language'),

    url(r'^common$', views.CommonView.as_view(), name='common'),
    url(r'^index$', views.IndexView.as_view(), name='index'),
    url(r'^about_us$', views.AboutUsView.as_view(), name='about-us'),
    url(r'^privacy$', views.PrivacyView.as_view(), name='privacy'),
    url(r'^tutorials$', views.TutorialListView.as_view(), name='tutorial-list'),

    url(r'^about_xltn$', views.AboutUsXLTNView.as_view(), name='about-xltn'),

    url(r'^admin_common$', views.AdminCommonView.as_view(), name='admin-common'),
    url(r'^admin_about$', views.AdminAboutUsView.as_view(), name='admin-about'),
    url(r'^admin_about_update$', views.AdminAboutUsUpdate.as_view(), name='admin-about-update'),

    url(r'^admin_privacy$', views.AdminPrivacyView.as_view(), name='admin-privacy'),
    url(r'^admin_privacy_update$', views.AdminPrivacyUpdate.as_view(), name='admin-privacy-update'),

    url(r'^admin_tutorials$', views.AdminTutorialListView.as_view(), name='admin-tutorial-list'),
    url(r'^admin_tutorial_create$', views.AdminTutorialCreateView.as_view(), name='admin-tutorial-create'),
    url(r'^admin_tutorial_update$', views.AdminTutorialUpdateView.as_view(), name='admin-tutorial-update'),

    url(r'^admin_banners$', views.AdminBannerListView.as_view(), name='admin-banner-list'),
    url(r'^admin_banner_create$', views.AdminBannerCreateView.as_view(), name='admin-banner-create'),
    url(r'^admin_banner_update$', views.AdminBannerUpdateView.as_view(), name='admin-banner-update'),
    url(r'^admin_banner_active$', views.AdminBannerActiveView.as_view(), name='admin-banner-active'),
]