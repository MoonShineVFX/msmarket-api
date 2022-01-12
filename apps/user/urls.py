from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^register$', views.RegisterView.as_view(), name='register'),
    url(r'^login$', views.ObtainTokenView.as_view(), name='login'),
    url(r'^guest_login$', views.ObtainTokenView.as_view(), name='guest-login'),
    #url(r'^forget_password$', views.ForgetPasswordView.as_view(), name='forget-password'),
    #url(r'^reset_password$', views.ResetPasswordView.as_view(), name='reset-password'),

    url(r'admin_accounts$', views.AdminUserList.as_view(), name='admin-account-list'),
    url(r'admin_account_search$', views.AdminUserSearch.as_view(), name='admin-account-search'),
    url(r'admin_account_create$', views.AdminUserCreate.as_view(), name='admin-account-create'),
    url(r'admin_account_update$', views.AdminUserUpdate.as_view(), name='admin-account-update'),
]