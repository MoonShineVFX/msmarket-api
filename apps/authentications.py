import requests
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from dj_rest_auth.jwt_auth import JWTCookieAuthentication
from django.utils.translation import gettext_lazy as _

from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed


class AdminJWTAuthentication(JWTCookieAuthentication):
    scope = "admin"

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        """
        Attempts to find and return a user using the given validated token.
        """
        try:
            scope = validated_token['scope']
        except KeyError:
            raise InvalidToken(_('Token contained no recognizable scope'))
        if scope != self.scope:
            raise InvalidToken(_('Invalid scope'))

        return user


class CustomerJWTAuthentication(JWTCookieAuthentication):
    scope = "customer"

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        """
        Attempts to find and return a user using the given validated token.
        """
        try:
            scope = validated_token['scope']
        except KeyError:
            raise InvalidToken(_('Token contained no recognizable scope'))
        if scope != self.scope:
            raise InvalidToken(_('Invalid scope'))

        return user


def recaptcha_valid_or_401(body):
    recaptcha_response = body.get('recaptcha', None)
    if recaptcha_response:
        url = 'https://www.google.com/recaptcha/api/siteverify'
        values = {
            'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response
        }
        response = requests.post(url, data=values, timeout=3)

        if response.json().get("success", False):
            return
    raise AuthenticationFailed('Invalid reCAPTCHA.')