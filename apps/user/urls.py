from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^register$', views.RegisterView.as_view(), name='register'),
    url(r'^login$', views.ObtainTokenView.as_view(), name='login'),
    url(r'^guest_login$', views.ObtainTokenView.as_view(), name='guest_login'),
    #url(r'^forget_password$', views.ForgetPasswordView.as_view(), name='forget-password'),
    #url(r'^reset_password$', views.ResetPasswordView.as_view(), name='reset-password'),
]