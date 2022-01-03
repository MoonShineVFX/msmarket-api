from decimal import Decimal
from collections import OrderedDict
from django.test import TestCase
from rest_framework.test import APIClient
from django.test.utils import override_settings
from ..shortcuts import debugger_queries
from .models import Product, Model, Renderer, Format
from ..user.models import User
from ..category.models import Tag
from ..order.models import Order


class ProductTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(id=1, name="user01", email="user01@mail.com")
        t1 = Tag.objects.create(id=1, name="tag01", creator_id=1)
        t2 = Tag.objects.create(id=2, name="tag02", creator_id=1)

        Renderer.objects.create(id=1, name="renderer01")
        Renderer.objects.create(id=2, name="renderer02")

        Format.objects.create(id=1, name="format01")
        Format.objects.create(id=2, name="format02")

        p1 = Product.objects.create(id=1, title="product01", preview="", description="", price=Decimal(1), model_size=0,
                               model_count=4, texture_size=0, status=0, creator_id=1)
        p2 = Product.objects.create(id=2, title="product02", preview="", description="", price=Decimal(1), model_size=0,
                               model_count=4, texture_size=0, status=0, creator_id=1)
        p1.tags.add(t1, t2)
        p2.tags.add(t1)

        Model.objects.create(id=1, size=0, product_id=1, format_id=1, renderer_id=1, creator_id=1)
        Model.objects.create(id=2, size=0, product_id=1, format_id=1, renderer_id=2, creator_id=1)

        Model.objects.create(id=3, size=0, product_id=1, format_id=2, renderer_id=1, creator_id=1)

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_get_web_product_list(self):
        url = '/api/web_products'
        response = self.client.get(url)
        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_get_web_product_list_with_tags(self):
        url = '/api/web_products?tags=1'
        response = self.client.get(url)
        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_get_web_product_detail(self):
        url = '/api/web_products/1'
        response = self.client.get(url)
        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_get_my_products(self):
        Product.objects.create(id=3, title="product03", preview="", description="", price=Decimal(1), model_size=0,
                               model_count=4, texture_size=0, status=0, creator_id=1)
        order = Order.objects.create(
            user=self.user, status=Order.SUCCESS, merchant_order_no="MSM20211201000001", amount=1000)
        order.products.set([1, 2])

        order = Order.objects.create(
            user=self.user, status=Order.SUCCESS, merchant_order_no="MSM20211201000002", amount=1000)
        order.products.set([1])

        order = Order.objects.create(
            user=self.user, status=Order.UNPAID, merchant_order_no="MSM20211201000003", amount=1000)
        order.products.set([3])

        url = '/api/my_products'
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        print(response.data)
        assert response.status_code == 200
        assert len(response.data) == 2

        expect = [
            OrderedDict([('id', 1), ('title', 'product01'), ('imgUrl', None), ('fileSize', 0),
                         ('models', [OrderedDict(
            [('id', 1), ('formatId', 1), ('formatName', 'format01'), ('rendererId', 1), ('rendererName', 'renderer01'),
             ('size', 0)]), OrderedDict(
            [('id', 2), ('formatId', 1), ('formatName', 'format01'), ('rendererId', 2), ('rendererName', 'renderer02'),
             ('size', 0)]), OrderedDict(
            [('id', 3), ('formatId', 2), ('formatName', 'format02'), ('rendererId', 1), ('rendererName', 'renderer01'),
             ('size', 0)])])]),
         OrderedDict([('id', 2), ('title', 'product02'), ('imgUrl', None), ('fileSize', 0), ('models', [])])]
        assert response.data == expect
