from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from ..category.models import Tag
from ..user.models import User
from ..product.models import Product
from .models import Banner, Tutorial, AboutUs, Privacy
from ..product.tests import get_test_image_file

from django.test.utils import override_settings
from ..shortcuts import debugger_queries


class IndexTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create(id=2, name="admin", email="admin@mail.com", is_staff=True)
        self.user = User.objects.create(id=1, name="user01", email="user01@mail.com")
        Tag.objects.create(id=1, name="tag01", creator=self.user)
        Tag.objects.create(id=2, name="tag02", creator=self.user)

        p1 = Product.objects.create(id=1, title="product01", description="", price=Decimal(1), model_size=0,
                                    model_count=4, texture_size=0, creator_id=1)
        p2 = Product.objects.create(id=2, title="product02", description="", price=Decimal(1), model_size=0,
                                    model_count=4, texture_size=0, creator_id=1)

        Banner.objects.create(id=1, title="banner01", creator=self.user, is_active=True)
        Banner.objects.create(id=2, title="banner02", creator=self.user, is_active=True)
        Banner.objects.create(id=3, title="banner03", creator=self.user, is_active=False)

        AboutUs.objects.create(id=1, title="AboutUs", description="description", creator=self.user)

        Privacy.objects.create(id=1, detail="detail", creator=self.user)

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
        assert len(response.data["banners"]) == 2

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_about_us(self):
        url = '/api/about_us'
        response = self.client.post(url)
        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_privacy(self):
        url = '/api/privacy'
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

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_common(self):
        url = '/api/admin_common'
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url)
        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_about_us(self):
        url = '/api/admin_about'
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url)
        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_privacy(self):
        url = '/api/admin_privacy'
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url)
        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_about_us_update(self):
        url = '/api/admin_about_update'
        data = {
            "title": "標題",
            "description": "描述",
            "file": get_test_image_file(),
            "supportModels": 3,
            "supportFormats": 15,
            "supportRenders": 50,
        }
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, data=data, format="multipart")
        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_privacy_update(self):
        url = '/api/admin_privacy_update'
        data = {
            "detail": "描述",
        }
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_tutorial_create(self):
        url = '/api/admin_tutorial_create'
        data = {
            "title": "標題",
            "file": get_test_image_file(),
            "link": "https://www.facebook.com",
        }
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, data=data, format="multipart")
        print(response.data)
        assert response.status_code == 201
        assert Tutorial.objects.filter(title="標題", link="https://www.facebook.com", creator_id=self.admin.id).exists()

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_tutorials(self):
        url = '/api/admin_tutorials'

        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url)
        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_tutorial_create(self):
        url = '/api/admin_tutorial_create'
        data = {
            "title": "標題",
            "file": get_test_image_file(),
            "link": "https://www.facebook.com",
        }
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, data=data, format="multipart")
        print(response.data)
        assert response.status_code == 201
        assert Tutorial.objects.filter(title="標題", link="https://www.facebook.com", creator_id=self.admin.id).exists()

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_tutorial_update(self):
        url = '/api/admin_tutorial_update'
        data = {
            "id": 1,
            "title": "新標題",
            "file": get_test_image_file(),
            "link": "https://www.facebook.com",
        }
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, data=data, format="multipart")
        print(response.data)
        assert response.status_code == 200
        assert Tutorial.objects.filter(
            id=1, title="新標題", link="https://www.facebook.com", updater_id=self.admin.id).exists()

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_banners(self):
        url = '/api/admin_banners'

        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url)
        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_banner_create(self):
        url = '/api/admin_banner_create'
        data = {
            "title": "標題",
            "file": get_test_image_file(),
            "link": "https://www.facebook.com",
            'description': "des",
            "isActive": True
        }
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, data=data, format="multipart")
        print(response.data)
        assert response.status_code == 201
        banner = Banner.objects.filter(
            title="標題", link="https://www.facebook.com", creator_id=self.admin.id, is_active=True).first()
        assert banner is not None
        assert banner.active_at is not None

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_banner_update(self):
        url = '/api/admin_banner_update'
        data = {
            "id": 1,
            "title": "新標題",
            "file": get_test_image_file(),
            "link": "https://www.facebook.com",
            "isActive": False
        }
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, data=data, format="multipart")
        print(response.data)
        assert response.status_code == 200
        banner = Banner.objects.filter(
            id=1, title="新標題", link="https://www.facebook.com", updater_id=self.admin.id, is_active=False).first()
        assert banner is not None
        assert banner.inactive_at is not None

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_banner_active(self):
        url = '/api/admin_banner_active'
        data = {
            "id": 1,
            "isActive": False
        }
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, data=data, format="multipart")
        print(response.data)
        assert response.status_code == 200
        banner = Banner.objects.filter(id=1, updater_id=self.admin.id, is_active=False).first()
        assert banner is not None
        assert banner.inactive_at is not None