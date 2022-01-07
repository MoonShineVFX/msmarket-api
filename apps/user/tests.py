from django.test import TestCase
from rest_framework.test import APIClient
from .models import User

from django.test.utils import override_settings
from ..shortcuts import debugger_queries


class UserTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create(id=2, name="admin", email="admin@mail.com", is_staff=True)
        self.admin_2 = User.objects.create(id=3, name="admin2", email="admin2@mail.com", is_staff=True, is_superuser=True)
        self.user = User.objects.create(id=1, name="user01", email="user01@mail.com")

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_register(self):
        url = '/api/register'
        data = {
            "realName": "realName",
            "nickname": "nickName",
            "email": "test@mail.com",
            "password": "password"
        }
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 200
        assert User.objects.filter(name="realName", nick_name="nickName", email="test@mail.com").exists()

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_login(self):
        url = '/api/login'
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url)
        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_accounts(self):
        url = '/api/admin_accounts'
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url)
        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_account_search(self):
        url = '/api/admin_account_search'
        self.client.force_authenticate(user=self.admin)
        data = {
            "query": "admin2",
        }
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 200