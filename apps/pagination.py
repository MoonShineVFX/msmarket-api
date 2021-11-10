from rest_framework.pagination import PageNumberPagination
from collections import OrderedDict
from apps.category.models import category
from rest_framework.response import Response


class ProductPagination(PageNumberPagination):
    page_size = 40
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('categories', category),
            ('products', data)
        ]))