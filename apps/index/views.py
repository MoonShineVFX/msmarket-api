from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..category.models import Tag
from ..category.serializers import TagNameOnlySerializer


class CommonView(APIView):

    def post(self, request):
        tags = Tag.objects.all()

        data = {
            "userId": request.user.id if request.user.is_authenticated else None,
            "userName": request.user.name if request.user.is_authenticated else None,
            "tags": TagNameOnlySerializer(tags, many=True).data,
        }

        return Response(data, status=status.HTTP_200_OK)