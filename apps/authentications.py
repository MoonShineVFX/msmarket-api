from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils.translation import gettext_lazy as _

from rest_framework_simplejwt.exceptions import InvalidToken


class AdminJWTAuthentication(JWTAuthentication):
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


class CustomerJWTAuthentication(JWTAuthentication):
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