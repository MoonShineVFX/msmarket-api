from django.conf import settings
from django.utils import timezone
from django.db.models import Prefetch
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView
from ..shortcuts import PostListView, PostCreateView, PostUpdateView, WebUpdateView
from rest_framework.response import Response
from rest_framework import status

from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.authentication import BasicAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from django.shortcuts import get_object_or_404
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail

from .models import User, AdminProfile
from ..order.models import Cart
from . import serializers


class RegisterView(APIView):
    def post(self, request):
        serializer = serializers.RegisterCustomerSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            token = str(refresh.access_token)
            self.merge_cart(user=user)
            response = Response({}, status=status.HTTP_200_OK)
            response.set_cookie(key="token", value=token, httponly=False, max_age=60 * 60, secure=False,
                                samesite="Strict")
            return response
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def merge_cart(self, user=None):
        """
        當初次登入時合併訪客購物車
        """
        user = user if user else self.request.user
        if "token" not in self.request.COOKIES and self.request.session.session_key:
            Cart.objects.filter(session_key=self.request.session.session_key).update(user=user)


class ObtainTokenView(APIView):
    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return self.post(request)

    def post(self, request):
        user = request.user
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        self.merge_cart()
        response = Response({"token": token}, status=status.HTTP_200_OK)
        response.set_cookie(key="token", value=token, httponly=False, max_age=60*60, secure=False, samesite="Strict")
        return response

    def merge_cart(self, user=None):
        """
        當初次登入時合併訪客購物車
        """
        user = user if user else self.request.user
        if "token" not in self.request.COOKIES and self.request.session.session_key:
            Cart.objects.filter(session_key=self.request.session.session_key).update(user=user)


class GuestLogin(APIView):
    def post(self, request):
        serializer = serializers.RegisterCustomerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
        return Response(status=status.HTTP_200_OK)


class CustomerAccountDetailView(RetrieveAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = serializers.CustomerSerializer

    def post(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def get_object(self):
        return self.request.user


class CustomerAccountUpdateView(WebUpdateView):
    permission_classes = (IsAuthenticated, )
    serializer_class = serializers.CustomerSerializer

    def get_object(self):
        return self.request.user


class ActiveAccountView(APIView):
    def post(self, request):
        serializer = serializers.ForgetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = get_object_or_404(User, email=email)
            token = default_token_generator.make_token(user)
            body = '親愛的會員您好：\n' \
                   '收到這封電子郵件，表示您嘗試透過忘記密碼功能重置密碼，若您未使用此功能，表示有其他人輸入錯誤信箱，請直接刪除即可。\n' \
                   '密碼重置網址，點擊後重置為預設密碼: {0}/resetmail.html?user={1}&password_reset={2}/\n' \
                   '＊網址有效期限為系統發行3天內\n' \
                   '此郵件為系統自動寄發，請勿直接回覆。'.format(settings.DASHBOARD_ROOT, user.id, token)
            send_mail('moonshine模型庫 忘記密碼重置信', body, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class ForgetPasswordView(APIView):
    def post(self, request):
        serializer = serializers.ForgetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.filter(email=email).first()
            if user:
                token = default_token_generator.make_token(user)
                body = '親愛的會員您好：\n' \
                       '收到這封電子郵件，表示您嘗試透過忘記密碼功能重置密碼，若您未使用此功能，表示有其他人輸入錯誤信箱，請直接刪除即可。\n' \
                       '密碼重置網址，點擊後重置密碼: {0}/reset_password?uid={1}&token={2}\n' \
                       '＊網址有效期限為系統發行3天內\n' \
                       '此郵件為系統自動寄發，請勿直接回覆。'.format(settings.API_HOST, user.id, token)
                send_mail('moonshine模型庫 忘記密碼重置信', body, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    def post(self, request):
        serializer = serializers.ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            uid = serializer.validated_data['uid']
            token = serializer.validated_data['token']
            password = serializer.validated_data['password']
            user = User.objects.filter(id=uid).first()

            if user and default_token_generator.check_token(user, token):
                user.set_password(password)
                user.password_updated_at = timezone.now()
                user.save()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
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
admin_queryset = User.objects.prefetch_related(Prefetch('admin_profile', queryset=admin_profile)).filter(is_staff=True)


class AdminUserList(PostListView):
    serializer_class = serializers.AdminUserSerializer
    admin_profile = AdminProfile.objects.select_related("creator", "updater")
    queryset = admin_queryset


class AdminUserSearch(AdminUserList):
    def filter_queryset(self, queryset):
        query = self.request.data.get('query', None)
        if query:
            queryset = queryset.filter(email__icontains=query)
        return queryset


class AdminUserCreate(PostCreateView):
    serializer_class = serializers.AdminUserCreateSerializer
    queryset = admin_queryset


class AdminUserUpdate(PostUpdateView):
    serializer_class = serializers.AdminUserUpdateSerializer
    queryset = admin_queryset