import base64
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
from ..user.models import User, CustomerProduct
from ..category.models import Tag
from ..order.models import Order

from .views import ModelDownloadLink


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

        p1 = Product.objects.create(id=1, title="商品01", title_zh="商品01", title_en="product01",
                                    description="", price=Decimal(1), model_size=0,
                               model_count=4, texture_size="1920x1080", is_active=True, creator_id=1)
        p2 = Product.objects.create(id=2, title="商品02", title_zh="商品02", title_en="product02",
                                    description="", price=Decimal(1), model_size=0,
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
        assert len(response.data["products"]) == 2

    def test_get_product_list_inactive(self):
        Product.objects.filter(id=1).update(is_active=False)
        url = '/api/products'
        response = self.client.get(url)
        print(response.data)
        assert response.status_code == 200
        assert len(response.data["products"]) == 1

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
        Image.objects.create(id=1, product_id=1, file=get_upload_file(file_type='.jpg'), position_id=2, creator_id=1, size=0)
        Product.objects.filter(id=1).update(main_image_id=1)
        url = '/api/products/1'
        response = self.client.get(url)
        print(response.data)
        assert response.data["imgUrl"] is not None
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_get_my_products(self):
        Product.objects.create(id=3, title="product03", description="", price=Decimal(1), model_size=0,
                               model_count=4, texture_size="1800x1800", creator_id=1)
        order = Order.objects.create(
            user=self.user, status=Order.SUCCESS, merchant_order_no="MSM20211201000001", amount=1000)
        order.products.set([1, 2])

        CustomerProduct.objects.create(user=self.user, order=order, product_id=1)
        CustomerProduct.objects.create(user=self.user, order=order, product_id=2)

        print("test start")
        url = '/api/my_products?lang=en'
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
    def test_model_download_link_user_has_product(self):

        order = Order.objects.create(
            user=self.user, status=Order.SUCCESS, merchant_order_no="MSM20211201000002", amount=1000)
        order.products.set([1])

        assert ModelDownloadLink().user_has_product(user_id=self.user.id, product_id=1)
        assert not ModelDownloadLink().user_has_product(user_id=self.user.id, product_id=2)

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
    def test_admin_upload_image_as_main_again(self):
        Image.objects.create(id=1, product_id=1, file=get_upload_file(file_type='.jpg'), position_id=2, creator_id=1, size=0)
        Product.objects.filter(id=1).update(main_image_id=1)

        url = '/api/admin_image_upload'
        data = {
            'productId': 1,
            'positionId': 2,
            "file": get_test_image_file(),
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data=data, format='multipart')
        print(response.data)
        assert response.status_code == 400

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_image_delete(self):
        Image.objects.create(id=1, product_id=1, file=get_upload_file(file_type='.jpg'), position_id=2, creator_id=1, size=0)
        url = '/api/admin_image_delete'
        data = {
            'id': 1,
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data=data, format='json')
        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_product_xltn(self):
        url = '/api/product_xltn'
        data = {
            'id': 1,
        }
        response = self.client.post(url, data=data, format='json')
        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_get_product_list_with_lang(self):
        url = '/api/products?lang=en'
        response = self.client.get(url)
        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_get_product_detail_with_lang(self):
        url = '/api/products/1?lang=en'
        response = self.client.get(url)
        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_get_my_products_with_lang(self):
        order = Order.objects.create(
            user=self.user, status=Order.SUCCESS, merchant_order_no="MSM20211201000001", amount=1000)
        order.products.set([1, 2])

        CustomerProduct.objects.create(user=self.user, order=order, product_id=1)
        CustomerProduct.objects.create(user=self.user, order=order, product_id=2)

        print("test start")
        url = '/api/my_products?lang=en'
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def _test_admin_model_upload_uri(self):
        Format.objects.create(id=3, name="format02")
        Renderer.objects.create(id=4, name="renderer02")
        Product.objects.create(id=8, title="商品08", title_zh="商品08", title_en="product08",
                                    description="", price=Decimal(1), model_size=0,
                               model_count=0, texture_size="1920x1080", is_active=True, creator_id=1)
        url = '/api/admin_model_upload_uri'
        data = {
            "productId": 8,
            "formatId": 3,
            "rendererId": 4,
            "size": 3710699725,
            "filename": "7z_UnderSea_PackA_FBX.7z",
        }
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_convert_key_to_base64(self):
        s = "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDgJOddYeqDwB3D\nWOQZA56sJgobwfko8z7mCb2Ih1NIC6kuu4zyFWjm9MYZUljZpL3PYRZ0xHYVBqsw\n9UqDp6o3IdaufsQiWhhxiycD0JCa7BHRv5gQmAhInYMokl7F1cvAZtdKlCxLuqKC\nYzw9DtYALOd20ChEhpy2cbv0F4JJuOeRI7F+wUBo0U+8fNlfkl4U/Zc8dKd7148J\nbq9QZG0RcMtI9K+JyhXBoHjHNR3TQVKIRfK2LeZVcRnpauombpvc33S9LblJkVKP\ntcQntSlP8IlZlyMT7MQ6QKdWiLSHHW7mONfqscdaDs1rToNEpdHWwqzc0v2YRDxP\nLD7bsrsPAgMBAAECggEATqtlMRde0iMpzxhx5n2owU8QmTF5m+/UEbU1eqfUiSLe\nnHJjQ8xT50veA6EtYiY6IIE4+n7B2xteFm7hWlgMnBEaYmBHwq7QiXmHlgUr29Qj\nZPTUEG7r6WCvWhwVe2ZQfxUZVymual31D8J4sA12+tTH4KGqoHKGqlo8160wo2LE\nO6PV5pJ3K8R78jySgeHqWBZs5Cv/1He76SAl4gJk7LRe7p2hesMy0s/hP8u2l6Ur\nOynvPz8znLm6eeXmindtYlz0aL9BEFytGNc63Q5Nf4MvXLi2YnWU8XuwCNj5cDyv\nSfdIMu6WuJofs10NuJ6RsnrRMeRCf6CW1pd+oV6y4QKBgQD7UldMFQNM38WUJf4N\nwGcGCwNS96KwrIYkL0By2kGFBCV2RS1P8xgRLvRN/xUmbt2sQQ3ZMUhd7vzR/3sl\nYiIRFg5c7DMXweh6hxT1+ZHztF8DpOWAVVpfVupdGlL/DgyGgIrl7dSk6Z8BK0Lx\nHu+zZSbqaD+6pYfw1PWoUlVNFwKBgQDkUQzL3cvG51D2E4pLhDs2RarhY1PHNwyt\ndrRsj6/AJtVGVcv1KhBx4u4vuhGa5CLMq9EJR3quLKe1O0nvRvtGwXLXEYLsriuf\nAv41CRuinJtlQNuJd61yAkrPSwuXf7hYQ2qnmJQbWP0YHUSyj1lcx4WurnoPYCBG\n202RYpjsyQKBgQC1xwbRRtmOPsQ/tYMeGy3pFwoednK76u1TOsIY0HhXZ3pZIwv1\nKdUciKO3zmpT1BiNwLftglHfbz55/ZnqniIZzaQx3b3OzzgBd7bXet3wMWQP1LMS\nsameD9WP5bxmMpkop8zPJciKR1f0ln/iuweQ7/bH0QNXUucScFYGmxaLnQKBgCSw\n8cGBb1ITsmsZUMw5/9oE8CUwdTI6oort3KjlnnTeyL944kIP9HyY33ZEDLg7mWwS\n4JEBL7H18y2ozYTqf08rn2z4n3Wxt8jiDkAvqoVDbaWj+qPo27LKs4MEqGQ8Xj+w\n9d7hIkwSzPmnGncnmlDSr6UW3P7Dj+xTKfAHTFQhAoGBAJQL2+kHh7Bv6G79Mg5F\nJ8uVu+qPdGFnMFZSciiwx7jA+bZFYtMZOJ3nTubsECXISdY/3x3fIGN+d7wDS6jS\nuCIn2iucXPh+RwreFr5mhZjVTTirih3mIsf0I1k5eUOp+ZEZkjpgKCBS4iv2EwLM\ng6YiMA5vqH/oG6oDuRqW55SP\n-----END PRIVATE KEY-----\n"
        b = s.encode("UTF-8")
        e = base64.b64encode(b)
        print(e)

