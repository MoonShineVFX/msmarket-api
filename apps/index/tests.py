from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from ..category.models import Tag
from ..user.models import User
from ..product.models import Product
from .models import Banner, Tutorial, AboutUs

from django.test.utils import override_settings
from ..shortcuts import debugger_queries


class IndexTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create(id=1, name="user01", email="user01@mail.com")
        Tag.objects.create(id=1, name="tag01", creator=self.user)
        Tag.objects.create(id=2, name="tag02", creator=self.user)

        p1 = Product.objects.create(id=1, title="product01", preview="", description="", price=Decimal(1), model_size=0,
                                    model_count=4, texture_size=0, status=0, creator_id=1)
        p2 = Product.objects.create(id=2, title="product02", preview="", description="", price=Decimal(1), model_size=0,
                                    model_count=4, texture_size=0, status=0, creator_id=1)

        Banner.objects.create(id=1, product=p1, creator=self.user)
        Banner.objects.create(id=2, product=p2, creator=self.user)

        AboutUs.objects.create(id=1, title="AboutUs", description="description", creator=self.user
                               )
        Tutorial.objects.create(id=1, title="tutorial01", creator=self.user, link="https://medium.com")
        Tutorial.objects.create(id=2, title="tutorial02", creator=self.user)

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_common(self):
        url = '/api/common'
        response = self.client.post(url)
        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_index(self):
        url = '/api/index'
        response = self.client.post(url)
        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_about_us(self):
        url = '/api/about_us'
        response = self.client.post(url)
        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_tutorials(self):
        url = '/api/tutorials'
        response = self.client.post(url)
        print(response.data)
        assert response.status_code == 200