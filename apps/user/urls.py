from django.conf.urls import url, include
from . import views
from dj_rest_auth.registration.views import RegisterView, VerifyEmailView
from dj_rest_auth.views import LoginView, PasswordResetView, PasswordResetConfirmView

urlpatterns = [
    url(r'^register$', views.RegisterView.as_view(), name='register'),
    url(r'^active_account$',
        views.CustomerActiveAccountView.as_view(), name='customer-active-account'),
    #url(r'^send_active_email$', views.SendCustomerActiveEmail.as_view(), name='send-active-email'),

    url(r'^login$', views.ObtainTokenView.as_view(), name='login'),
    url(r'^guest_login$', views.ObtainTokenView.as_view(), name='guest-login'),
    url(r'^google_login', views.GoogleLogin.as_view(), name='google-login'),

    url(r'^logout$', views.LogoutView.as_view(), name='logout'),
    url(r'^admin_logout$', views.AdminLogoutView.as_view(), name='admin-logout'),

    url(r'^admin_customers$', views.AdminCustomerView.as_view(), name='admin-customer-list'),

    url(r'^accounts/', include('allauth.urls'), name='socialaccount_signup'), # for socialaccount_signup reverse

    url(r'^my_account$', views.CustomerAccountDetailView.as_view(), name='customer-account-detail'),
    url(r'^account_update$', views.CustomerAccountUpdateView.as_view(), name='customer-account-update'),

    url(r'^forget_password$', views.CustomerForgetPasswordView.as_view(), name='customer-forget-password'),
    url(r'^reset_password$', views.CustomerResetPasswordView.as_view(), name='customer-reset-password'),
    url(r'^change_password$', views.CustomerChangePasswordView.as_view(), name='customer-change-password'),

    #url(r'^rest_register$', RegisterView.as_view(), name='rest-register'),
    #url(r'^verify_email/(?P<key>[-:\w]+)$', VerifyEmailView.as_view(), name='account_confirm_email'),
    #url(r'^rest_login$', LoginView, name='rest-login'),

    url(r'^admin_login$', views.AdminObtainTokenView.as_view(), name='admin-login'),
    url(r'^admin_accounts$', views.AdminUserList.as_view(), name='admin-account-list'),
    url(r'^admin_account_search$', views.AdminUserSearch.as_view(), name='admin-account-search'),
    url(r'^admin_account_create$', views.AdminUserCreate.as_view(), name='admin-account-create'),
    url(r'^admin_account_update$', views.AdminUserUpdate.as_view(), name='admin-account-update'),
    url(r'^admin_change_password$', views.AdminChangePasswordView.as_view(), name='admin-change-password'),
]