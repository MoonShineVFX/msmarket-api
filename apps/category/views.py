from rest_framework.views import APIView
from ..shortcuts import PostListView
from rest_framework import status
from rest_framework.response import Response
from .models import Tag
from . import serializers
from ..shortcuts import PostUpdateView, PostDestroyView
from rest_framework.permissions import IsAuthenticated, IsAdminUser


class AdminTagList(PostListView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminTagSerializer
    queryset = Tag.objects.select_related("creator", "updater").order_by("-updated_at", "-created_at").all()


class AdminTagCreate(APIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def post(self, request, *args, **kwargs):
        serializer = serializers.TagListCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(creator_id=self.request.user.id)

            tags = Tag.objects.select_related("creator", "updater").all()
            data = {
                "tags": serializers.AdminTagSerializer(tags, many=True).data,
            }
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminTagUpdate(PostUpdateView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    queryset = Tag.objects.select_related("creator", "updater").all()
    serializer_class = serializers.TagUpdateSerializer


class AdminTagDelete(PostDestroyView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    queryset = Tag.objects.select_related("creator", "updater").all()