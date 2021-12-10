from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import BasicAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from django.shortcuts import get_object_or_404
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail

from .models import User
from . import serializers


class RegisterView(APIView):
    def post(self, request):
        serializer = serializers.RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class ObtainTokenView(APIView):
    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return self.post(request)

    def post(self, request):
        user = request.user
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        response = Response({"token": token}, status=status.HTTP_200_OK)
        response.set_cookie(key="token", value=token, httponly=False, max_age=60*60, secure=False, samesite="Strict")
        return response


class ForgetPasswordView(APIView):
    def post(self, request):
        serializer = serializers.SendResetEmailSerializer(data=request.data)
        if serializer.is_valid():
            account = serializer.validated_data['account']
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


class ResetPasswordView(APIView):
    def post(self, request, pk, token):
        user = get_object_or_404(User.objects.only(
            'last_login', 'password', 'organization__password').select_related('organization'), id=pk)
        if default_token_generator.check_token(user, token):
            user.password = user.organization.password
            user.password_changed = None
            user.save(update_fields=['password', 'password_changed'])
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)
