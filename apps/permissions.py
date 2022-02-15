# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return 'scope' in request.auth.payload and request.auth.payload['scope'] == 'customer'


class IsSysAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        if not request.user.is_anonymous:
            if request.user.is_sys_auth:
                return True
        return False