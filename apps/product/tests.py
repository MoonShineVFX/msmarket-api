from decimal import Decimal
from collections import OrderedDict, Counter
from django.test import TestCase
from rest_framework.test import APIClient
from django.test.utils import override_settings
from ..shortcuts import debugger_queries

from unittest.mock import MagicMock
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import Product, Model, Renderer, Format, Image
from ..user.models import User
from ..category.models import Tag
from ..order.models import Order


def get_test_image_file():
    return SimpleUploadedFile(name='test_image.jpg', content=open('./mysite/test.jpeg', 'rb').read(),
                              content_type='image/jpeg')


def get_upload_file(filename="test", file_type=".zip"):
    file_mock = MagicMock(spec=File, name='FileMock')
    file_mock.name = '{}{}'.format(filename, file_type)
    return file_mock


class ProductTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create(id=2, name="admin", email="admin@mail.com", is_staff=True)
        self.user = User.objects.create(id=1, name="user01", email="user01@mail.com")
        t1 = Tag.objects.create(id=1, name="tag01", creator_id=1)
        t2 = Tag.objects.create(id=2, name="tag02", creator_id=1)

        Renderer.objects.create(id=1, name="renderer01")
        Renderer.objects.create(id=2, name="renderer02")

        Format.objects.create(id=1, name="format01")
        Format.objects.create(id=2, name="format02")

        p1 = Product.objects.create(id=1, title="product01", description="", price=Decimal(1), model_size=0,
                               model_count=4, texture_size="1920x1080", is_active=True, creator_id=1)
        p2 = Product.objects.create(id=2, title="product02", description="", price=Decimal(1), model_size=0,
                               model_count=4, texture_size="1920x1080", is_active=True, creator_id=1)
        p1.tags.add(t1, t2)
        p2.tags.add(t1)

        Model.objects.create(id=1, size=0, product_id=1, format_id=1, renderer_id=1, creator_id=1)
        Model.objects.create(id=2, size=0, product_id=1, format_id=1, renderer_id=2, creator_id=1)

        Model.objects.create(id=3, size=0, product_id=1, format_id=2, renderer_id=1, creator_id=1)

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_get_product_list(self):
        url = '/api/products'
        response = self.client.get(url)
        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_get_product_list_with_tags(self):
        url = '/api/products?tags=1'
        response = self.client.get(url)
        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_get_product_detail(self):
        url = '/api/products/1'
        response = self.client.get(url)
        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_get_my_products(self):
        Product.objects.create(id=3, title="product03", description="", price=Decimal(1), model_size=0,
                               model_count=4, texture_size="1800x1800", creator_id=1)
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
        assert response.data['list'] == expect

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_get_admin_product_list(self):
        url = '/api/admin_products'
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(url)
        print(response.data)
        assert response.status_code == 200
        response = self.client.post(url)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_get_admin_product_detail(self):
        url = '/api/admin_products/1'
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(url)
        print(response.data)
        assert response.status_code == 200
        response = self.client.post(url)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_product_create(self):
        url = '/api/admin_product_create'
        data = {
            "title": "title",
            "description": "description",
            "price": 1000,
            "modelSum": 2,
            "perImgSize": "1800x1800",
            "tags": [1, 2],
            "isActive": True
        }
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 201

        product = Product.objects.filter(title="title", price=1000, creator=self.admin).first()
        assert product is not None

        tags = [tag.id for tag in product.tags.all()]
        self.assertEqual(Counter(tags), Counter([1, 2]))

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_product_update(self):
        url = '/api/admin_product_update'
        data = {
            "id": 2,
            "title": "new_title",
            "description": "new_description",
            "price": 1000,
            "modelSum": 2,
            "perImgSize": "1800x1800",
            "tags": [1, 2],
            "isActive": True
        }
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, data=data, format="json")
        assert response.status_code == 200
        print(response.data)

        product = Product.objects.filter(id=2, title="new_title", price=1000, updater=self.admin).first()
        assert product is not None
        assert product.active_at is not None

        tags = [tag.id for tag in product.tags.all()]
        self.assertEqual(Counter(tags), Counter([1, 2]))

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_product_active(self):
        url = '/api/admin_product_active'
        data = {
            "id": 2,
            "isActive": False
        }
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, data=data, format="json")
        assert response.status_code == 200
        print(response.data)

        product = Product.objects.filter(id=2, is_active=False, updater_id=self.admin.id).first()
        assert product is not None
        assert product.active_at is None
        assert product.inactive_at is not None        

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_upload_image_as_preview(self):
        url = '/api/admin_image_upload'
        data = {
            'productId': 1,
            'positionId': 1,
            "file": get_test_image_file(),
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data=data, format='multipart')
        print(response.data)
        assert response.status_code == 201
        assert "url" in response.data
        img = Image.objects.first()
        assert img is not None
        assert img.size != 0

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_upload_image_as_main(self):
        url = '/api/admin_image_upload'
        data = {
            'productId': 1,
            'positionId': 2,
            "file": get_test_image_file(),
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data=data, format='multipart')
        print(response.data)
        assert response.status_code == 201
        assert "url" in response.data
        img = Image.objects.first()
        assert img is not None
        assert img.size != 0
        assert Product.objects.filter(id=1, main_image_id=img.id).exists()

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_image_delete(self):
        Image.objects.create(id=1, product_id=1, file=get_upload_file(file_type='.jpg'))
        url = '/api/admin_image_delete'
        data = {
            'id': 1,
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data=data, format='json')
        print(response.data)
        assert response.status_code == 200