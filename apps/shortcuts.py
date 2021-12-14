# -*- coding: utf-8 -*-
import uuid
import functools
import time
from django.utils import timezone

from django.shortcuts import get_object_or_404
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection, reset_queries

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


class PostCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated, )

    def perform_create(self, serializer):
        serializer.save(**{"creator_id": self.request.user.id})


class PostUpdateView(GenericAPIView, mixins.UpdateModelMixin):
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

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

    def get_extra_attrs(self):
        return {"creator_id": self.request.user.id}

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(**self.get_extra_attrs())
            data = {}
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WebUpdateView(GenericAPIView):
    permission_classes = (IsAuthenticated, )

    def get_extra_attrs(self):
        return {"updater_id": self.request.user.id, "updated_at": timezone.now()}

    def post(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(instance=instance, data=request.data)
        if serializer.is_valid():
            serializer.save(**self.get_extra_attrs())
            data = {}
            return Response(data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

