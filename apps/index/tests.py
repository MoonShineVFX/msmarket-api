from django.test import TestCase
from rest_framework.test import APIClient
from ..category.models import Tag
from ..user.models import User

from django.test.utils import override_settings
from ..shortcuts import debugger_queries


class IndexTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create(id=1, name="user01", email="user01@mail.com")
        Tag.objects.create(id=1, name="tag01", creator=self.user)
        Tag.objects.create(id=2, name="tag02", creator=self.user)

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_common(self):
        url = '/api/common'

        response = self.client.post(url)
        print(response.data)
        assert response.status_code == 200
