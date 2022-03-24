# -*- coding: utf-8 -*-
import uuid
import functools
import time
from django.utils import timezone
from django.conf import settings

from django.shortcuts import get_object_or_404
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection, reset_queries
from django.utils.translation import activate

from rest_framework.generics import GenericAPIView, CreateAPIView, DestroyAPIView
from rest_framework import mixins
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


def get_or_404(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ObjectDoesNotExist:
            raise Http404('No object matches the given ID.')
    return wrapper


def validate_pk(str):
    try:
        obj_id = uuid.UUID(str)
    except (TypeError, ValueError):
        raise Http404('ID format is wrong.')
    return obj_id


@get_or_404
def select_data_or_404(obj, str_id, *args, **kwargs):
    obj_id = validate_pk(str_id)
    if args or kwargs:
        if len(args) == 1:
            return obj.objects.values_list(*args, flat=True).filter(id=obj_id, **kwargs)
        else:
            return obj.objects.values_list(*args).filter(id=obj_id, **kwargs)
    else:
        return obj.objects.get(id=obj_id)


@get_or_404
def update_data_or_404(obj, str_id, *args, **kwargs):
    obj_id = validate_pk(str_id)
    obj.objects.filter(id=obj_id).update(*args, **kwargs)


def debugger_queries(func):
    """Basic function to debug queries."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print("func: ", func.__name__)
        reset_queries()

        start = time.time()
        start_queries = len(connection.queries)

        result = func(*args, **kwargs)

        end = time.time()
        end_queries = len(connection.queries)

        print("queries:", end_queries - start_queries)
        print("took: %.2fs" % (end - start))
        return result

    return wrapper


class PostListView(GenericAPIView):
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        data = {
            "list": serializer.data,
        }
        return Response(data, status=status.HTTP_200_OK)


class PostCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated, )

    def perform_create(self, serializer):
        serializer.save(**{"creator_id": self.request.user.id})


class PostUpdateView(GenericAPIView, mixins.UpdateModelMixin):
    permission_classes = (IsAuthenticated, )
    translation_serializer_class = None

    def post(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        lang_code = self.request.data.get("langCode", None)

        if lang_code:
            serializer = self.translation_serializer_class(instance=instance, data=request.data, partial=partial)
        else:
            serializer = self.serializer_class(instance=instance, data=request.data, partial=partial)

        serializer.is_valid(raise_exception=True)

        if lang_code:
            activate(lang_code)
            type(instance).objects.filter(id=instance.id).update(**serializer.validated_data)
        else:
            self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save(**{"updater_id": self.request.user.id, "updated_at": timezone.now()})

    def get_object(self):
        return get_object_or_404(self.queryset, id=self.request.data.get('id', None))


class PostDestroyView(DestroyAPIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except Exception:
            pass

    def get_object(self):
        return get_object_or_404(self.queryset, id=self.request.data.get('id', None))


class WebCreateView(GenericAPIView):
    permission_classes = (IsAuthenticated, )

    def perform_create(self, serializer):
        serializer.save(**{"creator_id": self.request.user.id})

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            data = {}
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WebUpdateView(GenericAPIView):
    permission_classes = (IsAuthenticated, )
    translation_serializer_class = None

    def perform_update(self, serializer):
        serializer.save(**{"updater_id": self.request.user.id, "updated_at": timezone.now()})

    def post(self, request, *args, **kwargs):
        instance = self.get_object()
        lang_code = self.request.data.get("langCode", None)

        if lang_code:
            serializer = self.translation_serializer_class(instance=instance, data=request.data, partial=True)
        else:
            serializer = self.serializer_class(instance=instance, data=request.data, partial=True)

        serializer.is_valid(raise_exception=True)

        if lang_code:
            activate(lang_code)
            type(instance).objects.filter(id=instance.id).update(**serializer.validated_data)
        else:
            self.perform_update(serializer)
        return Response({}, status=status.HTTP_200_OK)


class CreateActiveViewMixin(object):
    def perform_create(self, serializer):
        is_active = serializer.validated_data.get("is_active")
        data = {"creator_id": self.request.user.id}

        if is_active:
            data.update({"active_at": timezone.now()})
        else:
            data.update({"inactive_at": timezone.now()})

        serializer.save(**data)


class UpdateActiveViewMixin(object):
    def perform_update(self, serializer):
        data = {"updater_id": self.request.user.id, "updated_at": timezone.now()}

        is_active = serializer.validated_data.get("is_active", None)
        if is_active is not None:
            if is_active:
                data.update({"active_at": timezone.now()})
            else:
                data.update({"inactive_at": timezone.now()})

        serializer.save(**data)


class BaseXLTNView(GenericAPIView):
    serializer_class = None

    def get_object(self):
        return get_object_or_404(self.queryset, id=self.request.data.get('id', None))

    def post(self, request, *args, **kwargs):
        instance = self.get_object()

        data = dict()
        for lang in settings.LANGUAGES:
            lang_code = lang[0]
            activate(lang_code)
            lang_data = self.serializer_class(instance).data,
            data.update({lang_code: lang_data[0]})

        return Response(data, status=status.HTTP_200_OK)