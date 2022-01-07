from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^admin_tags$', views.AdminTagList.as_view(), name='admin-tag-list'),
    url(r'^admin_tag_create$', views.AdminTagCreate.as_view(), name='admin-tag-create'),
    url(r'^admin_tag_update$', views.AdminTagUpdate.as_view(), name='admin-tag-update'),
    url(r'^admin_tag_delete$', views.AdminTagDelete.as_view(), name='admin-tag-delete'),
]