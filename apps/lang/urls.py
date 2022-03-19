from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^lang_configs$', views.LangConfigListView.as_view(), name='lang-config-list'),
    url(r'^admin_lang_config_search$', views.AdminLangConfigSearchView.as_view(), name='admin-lang-config-search'),
    url(r'^admin_lang_config_update$', views.AdminLangConfigUpdateView.as_view(), name='admin-lang-config-update'),

]