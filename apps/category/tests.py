from django.test import TestCase
from rest_framework.test import APIClient
from django.test.utils import override_settings
from ..shortcuts import debugger_queries
from .models import Tag
from ..user.models import User
from ..lang.models import LangConfig


def setup_categories_tags(creator_id=1):
    Tag.objects.create(id=1, name="互動", name_zh="互動", name_en="VR", creator_id=creator_id)
    Tag.objects.create(id=2, name="5G網路", name_zh="5G網路", name_en="5G", creator_id=creator_id)


class TagTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        LangConfig.objects.create(lang="zh", updated_at="2020-10-01 00:00:00")
        LangConfig.objects.create(lang="en", updated_at="2020-01-01 00:00:00")

        self.user = User.objects.create(id=1, name="user01", email="user01@mail.com")
        self.admin = User.objects.create(id=2, name="admin", email="admin@mail.com", is_staff=True)
        setup_categories_tags()

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_get_tags_from_common_with_lang(self):
        url = '/api/common?lang=en'
        response = self.client.post(url)
        print(response.data)
        assert response.status_code == 200

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

        assert Tag.objects.filter(id=1, name_zh="新名稱", name="新名稱").exists()

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_tag_update_with_lang(self):
        url = '/api/admin_tag_update'
        data = {
            "langCode": "en",
            "id": 1,
            "name": "new",
        }
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, data=data, format='json')
        print(response.data)
        assert response.status_code == 200

        tag = Tag.objects.filter(id=1).raw_values().first()
        assert tag["name"] == "互動"
        assert tag["name_zh"] == "互動"
        assert tag["name_en"] == "new"

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

