from django.test import TestCase
from rest_framework.test import APIClient
from django.test.utils import override_settings
from ..shortcuts import debugger_queries
from .models import Tag
from ..user.models import User


def setup_categories_tags(creator_id=1):
    Tag.objects.create(id=1, name="互動", creator_id=creator_id)
    Tag.objects.create(id=2, name="5G", creator_id=creator_id)


class TagTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(id=1, name="user01", email="user01@mail.com")
        self.admin = User.objects.create(id=2, name="admin", email="admin@mail.com", is_staff=True)
        setup_categories_tags()

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_get_admin_tags(self):
        url = '/api/admin_tags'
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url)
        print(response.data)
        assert response.status_code == 200
        response = self.client.get(url)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_tag_create(self):
        url = '/api/admin_tag_create'
        data = {
            "tags": [
                {
                    "name": "互動2",

                },
                {
                    "name": "5G2",

                },
            ]
        }
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, data=data, format='json')
        print(response.data)
        assert response.status_code == 201
        assert Tag.objects.filter(name="互動2").exists()
        assert Tag.objects.filter(name="5G2").exists()

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_tag_update(self):
        url = '/api/admin_tag_update'
        data = {
            "id": 1,
            "name": "新名稱",
        }
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, data=data, format='json')
        print(response.data)
        assert response.status_code == 200

        assert Tag.objects.filter(id=1, name="新名稱").exists()

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_tag_delete(self):
        url = '/api/admin_tag_delete'
        data = {
            "id": 1,
        }
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, data=data, format='json')
        print(response.data)
        assert response.status_code == 200
        assert not Tag.objects.filter(id=1).exists()

