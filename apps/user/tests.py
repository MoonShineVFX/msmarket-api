from base64 import b64encode
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from .models import User, AdminProfile
from allauth.account.models import EmailAddress
from django.core import mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text
from django.contrib.auth.tokens import default_token_generator
from .views import reset_password_token_generator, active_account_token_generator

from django.test.utils import override_settings
from ..shortcuts import debugger_queries


class UserTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create(id=2, name="admin", email="admin@mail.com", is_staff=True)
        self.admin_2 = User.objects.create(id=3, name="admin2", email="admin2@mail.com", is_staff=True,
                                           is_superuser=True)
        self.user = User.objects.create(id=1, name="user01", email="user01@mail.com")
        deleted_admin = User.objects.create(id=4, name="deleted_admin", email="deleted_admin@mail.com", is_staff=True,
                                            is_superuser=True, is_deleted=True)

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
            "email": "test@mail.com",
            "password": "password"
        }
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 200
        assert User.objects.filter(email="test@mail.com").exists()
        assert EmailAddress.objects.filter(email="test@mail.com", primary=True, verified=False).exists()
        assert mail.outbox[0]
        print(mail.outbox[0].subject)
        print(mail.outbox[0].body)

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_register_with_exist_email(self):
        url = '/api/register'
        data = {
            "email": "admin@mail.com",
            "password": "password"
        }
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 400

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_active_account(self):
        url = '/api/register'
        data = {
            "email": "test@mail.com",
            "password": "password"
        }
        response = self.client.post(url, data=data, format="json")
        assert response.status_code == 200
        assert mail.outbox[0]
        print(mail.outbox[0].subject)

        user = User.objects.filter(email="test@mail.com").first()
        assert user
        assert not user.is_active
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = active_account_token_generator.make_token(user)

        url = '/api/active_account?uid={}&token={}'.format(uid, token)
        response = self.client.get(url)
        print(response.data)
        assert response.status_code == 200
        user = User.objects.filter(email="test@mail.com", email_verified=True).first()
        assert user is not None
        assert EmailAddress.objects.filter(email="test@mail.com", primary=True, verified=True).exists()
        assert user.is_active

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
    def _test_rest_login(self):
        url = '/api/rest_login'
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url)
        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def _test_send_active_email(self):
        EmailAddress.objects.create(user=self.user,  verified=False)

        basic_auth = b64encode(b"user01@mail.com:password").decode("ascii")

        url = '/api/send_active_email'
        auth_headers = {
            'HTTP_AUTHORIZATION': 'Basic %s' % basic_auth
        }
        response = self.client.post(url, **auth_headers)

        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_customer_login(self):
        self.body = {'recaptcha': '123'}

        url = '/api/login'
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data=self.body, format='json')
        print(response.data)
        print(response.client.cookies.items())
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_customer_login_with_deleted(self):
        self.user.is_deleted = True
        self.user.save()

        self.body = {'recaptcha': '123'}

        url = '/api/login'
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data=self.body, format='json')
        print(response.data)
        assert response.data['detail'] == '您没有执行该操作的权限。'
        assert response.status_code == 403

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_customer_login_without_email_verified_and_EmailAddress_verified(self):
        EmailAddress.objects.create(user=self.user,  verified=False)

        self.body = {'recaptcha': '123'}
        url = '/api/guest_login'
        auth_headers = {
            'HTTP_AUTHORIZATION': 'Basic dXNlcjAxQG1haWwuY29tOnBhc3N3b3Jk'
        }
        response = self.client.post(url, data=self.body, **auth_headers)

        print(response.data)
        assert response.status_code == 401

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_customer_login_without_email_verified(self):
        EmailAddress.objects.create(user=self.user,  verified=True)

        basic_auth = b64encode(b"user01@mail.com:password").decode("ascii")

        self.body = {'recaptcha': '123'}
        url = '/api/guest_login'
        auth_headers = {
            'HTTP_AUTHORIZATION': 'Basic %s' % basic_auth
        }
        response = self.client.post(url, data=self.body, **auth_headers)

        print(response.data)
        assert response.status_code == 401

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_customer_login_with_all_email_verified(self):
        EmailAddress.objects.create(user=self.user,  verified=True)
        self.user.email_verified = True
        self.user.save()

        basic_auth = b64encode(b"user01@mail.com:password").decode("ascii")

        self.body = {'recaptcha': '123'}
        url = '/api/guest_login'
        auth_headers = {
            'HTTP_AUTHORIZATION': 'Basic %s' % basic_auth
        }
        response = self.client.post(url, data=self.body, **auth_headers)

        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_customer_login_with_admin(self):
        self.body = {'recaptcha': '123'}

        url = '/api/login'
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, data=self.body, format='json')
        print(response.data)
        assert response.status_code == 403

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_rest_login_token(self):
        from dj_rest_auth.utils import jwt_encode
        self.access_token, self.refresh_token = jwt_encode(self.user)
        print(self.access_token)

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_JWT_scope(self):
        EmailAddress.objects.create(user=self.user, verified=True)
        self.user.email_verified = True
        self.user.save()

        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        refresh['scope'] = "customer"
        token = str(refresh.access_token)

        url = '/api/my_account'
        auth_headers = {
            'HTTP_AUTHORIZATION': 'Bearer ' + token,
        }
        response = self.client.post(url, **auth_headers)
        print(response.data)
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
    def test_forget_password_with_admin(self):
        url = '/api/forget_password'
        data = {
            "email": "admin01@mail.com",
        }
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 200
        assert not mail.outbox

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_forget_password_again_in_3_min(self):
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

        response = self.client.post(url, data=data, format="json")
        assert response.status_code == 400

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_reset_password_token(self):
        default_token = default_token_generator.make_token(self.user)
        assert not reset_password_token_generator.check_token(self.user, default_token)

        self.user.reset_mail_sent = timezone.now()
        my_token = reset_password_token_generator.make_token(self.user)
        assert reset_password_token_generator.check_token(self.user, my_token)

        # test when a new reset_mail is sent, old token is expired
        self.user.reset_mail_sent = timezone.now() + timedelta(minutes=1)
        assert not reset_password_token_generator.check_token(self.user, my_token)

        # test when password is changed, old token is expired
        self.user.reset_mail_sent = None
        self.user.password_updated_at = timezone.now()
        assert not reset_password_token_generator.check_token(self.user, my_token)

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_reset_password(self):
        url = '/api/reset_password'
        token = reset_password_token_generator.make_token(self.user)
        data = {
            "uid": urlsafe_base64_encode(force_bytes(self.user.pk)),
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
    def test_reset_password_again_with_same_token_after_changed(self):
        url = '/api/reset_password'
        token = reset_password_token_generator.make_token(self.user)
        data = {
            "uid": urlsafe_base64_encode(force_bytes(self.user.pk)),
            "token": token,
            "password": "new_password"
        }
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 200
        user = User.objects.get(id=self.user.id)
        assert user.check_password("new_password")
        assert user.password_updated_at

        response = self.client.post(url, data=data, format="json")
        assert response.status_code == 400

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
            "realName": "new",
        }
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 200
        assert User.objects.filter(id=self.user.id, real_name="new").exists()

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_customers(self):
        url = '/api/admin_customers'
        self.client.force_authenticate(user=self.admin)
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
        for user in response.data['list']:
            assert user['account'] != "deleted_admin@mail.com"

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_deleted_admin_perms(self):
        self.admin.is_deleted = True
        self.admin.save()

        url = '/api/admin_account_search'
        self.client.force_authenticate(user=self.admin)
        data = {
            "query": "admin2",
        }
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 403


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