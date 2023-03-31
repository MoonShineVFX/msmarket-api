from urllib.parse import urlparse

from django.conf import settings
from django.utils import timezone
from datetime import timedelta, datetime, time
from django.db.models import Prefetch, Sum, Case, When
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView
from ..shortcuts import PostListView, PostCreateView, PostUpdateView, WebUpdateView
from rest_framework.response import Response
from rest_framework import status

from rest_framework.permissions import IsAuthenticated, IsAdminUser
from ..authentications import AdminJWTAuthentication, CustomerJWTAuthentication, recaptcha_valid_or_401
from ..permissions import IsCustomer
from rest_framework.authentication import BasicAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.throttling import AnonRateThrottle

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode, base36_to_int
from django.utils.encoding import force_bytes, force_text
from django.utils.crypto import constant_time_compare
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail

from .models import User, AdminProfile
from ..order.models import Cart
from allauth.account.models import EmailAddress
from . import serializers

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView, SocialConnectView


class RegisterView(APIView):
    def post(self, request):
        serializer = serializers.RegisterCustomerSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            self.send_active_email(user=user)
            response = Response({}, status=status.HTTP_200_OK)
            return response
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def send_active_email(self, user):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = active_account_token_generator.make_token(user)
        body = '親愛的會員您好：\n' \
               '收到這封電子郵件，表示您註冊本網站會員，若您未使用此功能，表示有其他人輸入錯誤信箱。\n' \
               '帳號啟用信網址，點擊後啟用帳號: {0}/active_account?uid={1}&token={2}\n' \
               '＊網址有效期限為1天內\n' \
               '此郵件為系統自動寄發，請勿直接回覆。'.format(settings.API_HOST, uid, token)
        send_mail('moonshine模型庫 帳號啟用信', body, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)


class SendCustomerActiveEmail(RegisterView):
    authentication_classes = (BasicAuthentication,)
    permission_classes = ()

    def post(self, request):
        print(request.user)
        self.send_active_email(user=request.user)
        response = Response({}, status=status.HTTP_200_OK)
        return response


class ObtainTokenView(APIView):
    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated, IsCustomer)

    def get(self, request):
        return self.post(request)

    def post(self, request):
        recaptcha_valid_or_401(request.data)

        user = request.user
        refresh = RefreshToken.for_user(user)
        refresh['scope'] = "customer"
        token = str(refresh.access_token)
        self.merge_cart()
        response = Response({"token": token}, status=status.HTTP_200_OK)
        response.set_cookie(key="token", value=token, httponly=True, max_age=60*60, secure=True, samesite="None")
        return response

    def merge_cart(self, user=None):
        """
        當初次登入時合併訪客購物車
        """
        user = user if user else self.request.user
        if "token" not in self.request.COOKIES and self.request.session.session_key:
            Cart.objects.filter(session_key=self.request.session.session_key).update(user=user)


class AdminObtainTokenView(APIView):
    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated, IsAdminUser)

    def get(self, request):
        return self.post(request)

    def post(self, request):
        user = request.user
        refresh = RefreshToken.for_user(user)
        refresh['scope'] = "admin"
        token = str(refresh.access_token)
        response = Response({"token": token}, status=status.HTTP_200_OK)
        response.set_cookie(key="admin_token", value=token, httponly=False, max_age=60*60, secure=False, samesite="Strict")
        return response


class LogoutView(APIView):
    authentication_classes = [CustomerJWTAuthentication]
    permission_classes = (IsAuthenticated, )

    def post(self, request):
        request.session.clear()
        response = Response(status=status.HTTP_200_OK)
        response.delete_cookie('token')
        return response


class AdminLogoutView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, )

    def post(self, request):
        response = Response(status=status.HTTP_200_OK)
        response.delete_cookie('admin_token')
        return response


class CustomerAccountDetailView(RetrieveAPIView):
    authentication_classes = [CustomerJWTAuthentication]
    permission_classes = (IsAuthenticated, )
    serializer_class = serializers.CustomerSerializer

    def post(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def get_object(self):
        return self.request.user


class CustomerAccountUpdateView(WebUpdateView):
    authentication_classes = [CustomerJWTAuthentication]
    permission_classes = (IsAuthenticated, )
    serializer_class = serializers.CustomerSerializer

    def get_object(self):
        return self.request.user


class TimeLimitedTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        login_timestamp = '' if user.last_login is None else user.last_login.replace(microsecond=0, tzinfo=None)
        email_field = user.get_email_field_name()
        email = getattr(user, email_field, '') or ''
        password_updated_at = '' if user.password_updated_at is None else user.password_updated_at.replace(microsecond=0, tzinfo=None)
        reset_mail_sent = '' if user.reset_mail_sent is None else user.reset_mail_sent.replace(microsecond=0, tzinfo=None)
        return f'{user.pk}{user.password}login_timestamp={login_timestamp}{timestamp}{email}password_updated_at={password_updated_at}reset_mail_sent={reset_mail_sent}'


class ActiveAccountTokenGenerator(PasswordResetTokenGenerator):
    def check_token(self, user, token):
        """
        Check that a password reset token is correct for a given user.
        """
        if not (user and token):
            return False
        # Parse the token
        try:
            ts_b36, _ = token.split("-")
            # RemovedInDjango40Warning.
            legacy_token = len(ts_b36) < 4
        except ValueError:
            return False

        try:
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False

        # Check that the timestamp/uid has not been tampered with
        if not constant_time_compare(self._make_token_with_timestamp(user, ts), token):
            # RemovedInDjango40Warning: when the deprecation ends, replace
            # with:
            #   return False
            if not constant_time_compare(
                self._make_token_with_timestamp(user, ts, legacy=True),
                token,
            ):
                return False

        # RemovedInDjango40Warning: convert days to seconds and round to
        # midnight (server time) for pre-Django 3.1 tokens.
        now = self._now()
        if legacy_token:
            ts *= 24 * 60 * 60
            ts += int((now - datetime.combine(now.date(), time.min)).total_seconds())
        # Check the timestamp is within limit.
        if (self._num_seconds(now) - ts) > settings.EMAIL_VERIFICATION_TIMEOUT:
            return False

        return True

    def _make_hash_value(self, user, timestamp):
        email_field = user.get_email_field_name()
        email = getattr(user, email_field, '') or ''
        is_active = user.is_active
        return f'{user.pk}is_active={is_active}{timestamp}{email}'


reset_password_token_generator = TimeLimitedTokenGenerator()
active_account_token_generator = ActiveAccountTokenGenerator()


class CustomerForgetPasswordView(APIView):
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = serializers.ForgetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.filter(email=email, is_staff=False).first()
            if user:
                # reset mail can only be sent every 3 min
                if user.reset_mail_sent and timezone.now() - user.reset_mail_sent < timedelta(minutes=3):
                    return Response(status=status.HTTP_400_BAD_REQUEST)

                user.reset_mail_sent = timezone.now()
                user.save(update_fields=['reset_mail_sent'])
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = reset_password_token_generator.make_token(user)
                body = '親愛的會員您好：\n' \
                       '收到這封電子郵件，表示您嘗試透過忘記密碼功能重置密碼，若您未使用此功能，表示有其他人輸入錯誤信箱，請直接刪除即可。\n' \
                       '密碼重置網址，點擊後重置密碼: {0}/reset_password?uid={1}&token={2}\n' \
                       '＊網址有效期限為30分內\n' \
                       '此郵件為系統自動寄發，請勿直接回覆。'.format(settings.API_HOST, uid, token)
                send_mail('moonshine模型庫 忘記密碼重置信', body, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)

            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class CustomerResetPasswordView(APIView):
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = serializers.ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            uidb64 = serializer.validated_data['uid']
            token = serializer.validated_data['token']
            password = serializer.validated_data['password']

            try:
                uid = force_text(urlsafe_base64_decode(uidb64))
                user = User.objects.get(pk=uid, is_staff=False)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
                user = None

            if user and reset_password_token_generator.check_token(user, token):
                user.set_password(password)
                user.password_updated_at = timezone.now()
                user.save(update_fields=["password", "password_updated_at"])
                return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class CustomerActiveAccountView(APIView):
    throttle_classes = [AnonRateThrottle]

    def get(self, request):
        uidb64 = request.GET.get('uid', None)
        token = request.GET.get('token', None)
        if uidb64 and token:
            try:
                uid = force_text(urlsafe_base64_decode(uidb64))
                user = User.objects.get(pk=uid, is_staff=False)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
                user = None
            if user and active_account_token_generator.check_token(user, token):
                EmailAddress.objects.filter(user_id=user.id, email=user.email).update(verified=True)
                User.objects.filter(id=user.id).update(email_verified=True)
                return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class CustomerChangePasswordView(APIView):
    authentication_classes = [CustomerJWTAuthentication]
    permission_classes = (IsAuthenticated, )

    def post(self, request):
        serializer = serializers.ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            old_password = serializer.validated_data["password"]
            new_password1 = serializer.validated_data["new_password1"]
            new_password2 = serializer.validated_data["new_password2"]
            user = request.user
            if user.check_password(old_password) and new_password1 == new_password2:
                user.set_password(new_password1)
                user.password_updated_at = timezone.now()
                user.save(update_fields=['password', 'password_updated_at'])
                return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class AdminChangePasswordView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)

    def post(self, request):
        serializer = serializers.AdminChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            new_password = serializer.validated_data["password"]
            user = request.user
            user.set_password(new_password)
            user.password_updated_at = timezone.now()
            user.save(update_fields=['password', 'password_updated_at'])
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


admin_profile = AdminProfile.objects.select_related("creator", "updater")
admin_queryset = User.objects.prefetch_related(Prefetch('admin_profile', queryset=admin_profile)).filter(
    is_staff=True, is_deleted=False)


class AdminUserList(PostListView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminUserSerializer
    admin_profile = AdminProfile.objects.select_related("creator", "updater")
    queryset = admin_queryset


class AdminCustomerView(PostListView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminCustomerSerializer
    queryset = User.objects.filter(is_staff=False)


class AdminUserSearch(AdminUserList):
    def filter_queryset(self, queryset):
        query = self.request.data.get('query', None)
        if query:
            queryset = queryset.filter(email__icontains=query)
        return queryset


class AdminUserCreate(PostCreateView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminUserCreateSerializer
    queryset = admin_queryset


class AdminUserUpdate(PostUpdateView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminUserUpdateSerializer
    queryset = admin_queryset


CALLBACK_URL_YOU_SET_ON_GOOGLE = settings.API_HOST


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    serializer_class = serializers.GoogleSocialLoginSerializer
    callback_url = CALLBACK_URL_YOU_SET_ON_GOOGLE
    client_class = OAuth2Client


class GoogleConnect(SocialConnectView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = CALLBACK_URL_YOU_SET_ON_GOOGLE
    client_class = OAuth2Client