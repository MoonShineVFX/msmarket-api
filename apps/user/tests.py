from django.test import TestCase
from rest_framework.test import APIClient
from .models import User, AdminProfile

from django.core import mail
from django.contrib.auth.tokens import default_token_generator

from django.test.utils import override_settings
from ..shortcuts import debugger_queries


class UserTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create(id=2, name="admin", email="admin@mail.com", is_staff=True)
        self.admin_2 = User.objects.create(id=3, name="admin2", email="admin2@mail.com", is_staff=True, is_superuser=True)
        self.user = User.objects.create(id=1, name="user01", email="user01@mail.com")

        self.admin.set_password("password")
        self.admin.save()

        self.user.set_password("password")
        self.user.save()

        AdminProfile.objects.create(id=1, user_id=2, creator_id=2)
        AdminProfile.objects.create(id=2, user_id=3, creator_id=2)

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
    def test_register_with_exist_email(self):
        url = '/api/register'
        data = {
            "realName": "realName",
            "nickname": "nickName",
            "email": "admin@mail.com",
            "password": "password"
        }
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 400

    @override_settings(DEBUG=True)
    @debugger_queries
    def _test_rest_register(self):
        url = '/api/rest_register'
        data = {
            "username": "test@mail.com",
            "email": "test@mail.com",
            "password1": "TE$Tpa$$w0rd",
            "password2": "TE$Tpa$$w0rd"
        }
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        print(response.client.cookies.items())
        assert response.status_code == 201
        assert User.objects.filter(email="test@mail.com").exists()
        print(mail.outbox[0].subject)
        print(mail.outbox[0].body)
        assert mail.outbox[0]

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
    def test_JWT_scope(self):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        refresh['scope'] = "customer"
        token = str(refresh.access_token)

        url = '/api/my_account'
        auth_headers = {
            'HTTP_AUTHORIZATION': 'Bearer ' + token,
        }
        response = self.client.post(url, **auth_headers)
        assert response.status_code == 200

        refresh = RefreshToken.for_user(self.user)
        refresh['scope'] = "admin"
        token = str(refresh.access_token)
        auth_headers = {
            'HTTP_AUTHORIZATION': 'Bearer ' + token,
        }
        response = self.client.post(url, **auth_headers)
        print(response.data)
        assert response.status_code == 401

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_forget_password(self):
        url = '/api/forget_password'
        data = {
            "email": "user01@mail.com",
        }
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 200
        print(mail.outbox[0].subject)
        print(mail.outbox[0].body)
        assert mail.outbox[0]

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_reset_password(self):
        url = '/api/reset_password'
        token = default_token_generator.make_token(self.user)
        data = {
            "uid": self.user.id,
            "token": token,
            "password": "new_password"
        }
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 200
        user = User.objects.get(id=self.user.id)
        assert user.check_password("new_password")
        assert user.password_updated_at

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_change_password(self):
        url = '/api/change_password'

        data = {
            "password": "password",
            "newPassword": "new_password",
            "confirmNewPassword": "new_password",
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 200
        user = User.objects.get(id=self.user.id)
        assert user.check_password("new_password")
        assert user.password_updated_at

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_change_password_with_wrong_input(self):
        url = '/api/change_password'

        data = {
            "password": "wrong_password",
            "newPassword": "new_password",
            "confirmNewPassword": "new_password",
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 400
        user = User.objects.get(id=self.user.id)
        assert user.check_password("password")
        assert not user.password_updated_at

        data = {
            "password": "password",
            "newPassword": "new_password",
            "confirmNewPassword": "wrong_new_password",
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 400
        user = User.objects.get(id=self.user.id)
        assert user.check_password("password")
        assert not user.password_updated_at

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_my_account(self):
        url = '/api/my_account'
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url)
        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_account_update(self):
        url = '/api/account_update'
        self.client.force_authenticate(user=self.user)
        data = {
            "nickname": "new",
        }
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 200
        assert User.objects.filter(id=self.user.id, nick_name="new").exists()

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

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_account_create(self):
        url = '/api/admin_account_create'
        self.client.force_authenticate(user=self.admin)
        data = {
            "account": "new_admin@mail.com",
            "password": "password",
            "isAssetAdmin": True,
            "isFinanceAdmin": True,
            "isSuperuser": True,
        }
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 201
        user = User.objects.filter(email="new_admin@mail.com", is_staff=True).first()
        assert user is not None
        assert AdminProfile.objects.filter(user=user, is_asset_admin=True, is_finance_admin=True).exists()

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_account_update_customer(self):
        url = '/api/admin_account_update'
        self.client.force_authenticate(user=self.admin)
        data = {
            "id": self.user.id,
            "isAssetAdmin": True,
            "isFinanceAdmin": True,
            "isSuperuser": True,
        }
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 404
        assert User.objects.filter(id=self.user.id, is_staff=False, is_superuser=False).exists()

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_account_update_staff(self):
        url = '/api/admin_account_update'
        self.client.force_authenticate(user=self.admin)
        data = {
            "id": self.admin.id,
            "isAssetAdmin": True,
            "isFinanceAdmin": True,
            "isSuperuser": True,
        }
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 200
        assert User.objects.filter(id=self.admin.id, is_staff=True, is_superuser=True).exists()
        assert AdminProfile.objects.filter(user=self.admin, is_asset_admin=True, is_finance_admin=True).exists()

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

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_change_password(self):
        url = '/api/admin_change_password'
        self.client.force_authenticate(user=self.admin)
        data = {
            "password": "new_password",
        }
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 200
        admin = User.objects.get(id=self.admin.id)
        assert admin.password_updated_at is not None
        assert admin.check_password("new_password")