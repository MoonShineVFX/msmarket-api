import json
from collections import OrderedDict, Counter
from django.utils import timezone
from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from django.test.utils import override_settings, settings
from ..shortcuts import debugger_queries
from .models import Order, Cart, NewebpayResponse
from ..product.models import Product
from ..user.models import User

from .views import encrypt_with_SHA256, AESCipher
from urllib.parse import urlencode


class OrderTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(id=1, name="user01", email="user01@mail.com")

        p1 = Product.objects.create(id=1, title="product01", preview="", description="", price=Decimal(1), model_size=0,
                                    model_count=4, texture_size=0, status=0, creator_id=1)
        p2 = Product.objects.create(id=2, title="product02", preview="", description="", price=Decimal(1), model_size=0,
                                    model_count=4, texture_size=0, status=0, creator_id=1)

    @override_settings(DEBUG=True)
    def test_encrypt_with_AES_and_SHA(self):
        trade_info = {
            # 這些是藍新在傳送參數時的必填欄位
            "MerchantID": "MS12345567",
            "MerchantOrderNo": "2021120100001",
            "TimeStamp": timezone.now().timestamp(),
            "RespondType": "JSON",
            "Amt": 123,  # 訂單金額
            "Version": "1.6",
            "ItemDesc": "第一次串接就成功！",
            "Email": "1234another@gmail.com",
            "LoginType": 0,
            # --------------------------
            # 將要選擇的付款服務加上參數
            "CREDIT": 1,
            "VACC": 1,
            # 即時付款完成後，以 form post 方式要導回的頁面
            "ReturnURL": "商品訂單頁面",
            # 訂單完成後，以背景 post 回報訂單狀況
            "NotifyURL": "處理訂單的網址",
        }
        trade_info = urlencode(trade_info)
        c = AESCipher()
        result = c.encrypt(raw=trade_info)
        print(result)

        result = encrypt_with_SHA256(result)
        print(result)

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_order_create(self):
        Cart.objects.create(user_id=1, product_id=1)
        Cart.objects.create(user_id=1, product_id=2)

        url = '/api/order_create'
        data = {
            "cartIds": [1, 2]
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 200
        order = Order.objects.filter(user=self.user).last()
        assert order.amount == Decimal("2.000")

        order_product_ids = [product.id for product in order.products.all()]
        self.assertEqual(Counter(order_product_ids), Counter([1, 2]))

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_newebpay_payment_notify(self):
        url = '/api/newebpay_payment_notify'
        data = {
            "Status": "SUCCESS",
            "MerchantID": "MerchantID",
            "TradeInfo": "TradeInfo",
            "TradeSha": "TradeSha",
            "Version": "1.6"
        }
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 201
        assert NewebpayResponse.objects.filter(MerchantID="MerchantID").exists()

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_get_cart_products_without_login(self):
        url = '/api/cart_products'
        response = self.client.post(url)
        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_get_cart_products_with_login(self):
        Cart.objects.create(user_id=1, product_id=1)
        Cart.objects.create(user_id=1, product_id=2)

        url = '/api/cart_products'
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url)
        assert response.data == {
            'list': [OrderedDict([('id', 1), ('productId', 1), ('title', 'product01'), ('imgUrl', None), ('price', Decimal('1.0000'))]),
                     OrderedDict([('id', 2), ('productId', 2), ('title', 'product02'), ('imgUrl', None), ('price', Decimal('1.0000'))])],
            'amount': Decimal('2.0000')}
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_cart_product_add_with_login(self):
        url = '/api/cart_product_add'
        data = {
            "productId": 1
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 201
        assert Cart.objects.filter(user=self.user, product_id=1).exists()

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_cart_product_add_exist_product_with_login(self):
        Cart.objects.create(user_id=1, product_id=1)

        url = '/api/cart_product_add'
        data = {
            "productId": 1
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 201
        assert Cart.objects.filter(user=self.user, product_id=1).exists()
        assert Cart.objects.filter(user=self.user, product_id=1).count() == 1

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_cart_product_add_without_login(self):
        session = self.client.session

        url = '/api/cart_product_add'
        data = {
            "productId": 1
        }
        response = self.client.post(url, data=data, format="json")

        print(response.data)
        assert response.status_code == 201
        assert Cart.objects.filter(product_id=1, session_key=session.session_key).exists()

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_cart_product_add_exist_product_without_login(self):
        session = self.client.session
        Cart.objects.create(session_key=session.session_key, product_id=1)

        url = '/api/cart_product_add'
        data = {
            "productId": 1
        }
        response = self.client.post(url, data=data, format="json")

        assert response.status_code == 201
        assert Cart.objects.filter(product_id=1, session_key=session.session_key).exists()
        assert Cart.objects.filter(product_id=1, session_key=session.session_key).count() == 1

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_cart_product_merge_after_login(self):
        session = self.client.session
        Cart.objects.create(session_key=session.session_key, product_id=1)

        url = '/api/login'
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url)
        assert Cart.objects.filter(product_id=1, session_key=session.session_key, user=self.user).exists()

        url = '/api/cart_product_add'
        data = {
            "productId": 2
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data=data, format="json")

        assert response.status_code == 201
        assert Cart.objects.filter(product_id=2, user=self.user).exists()
        assert Cart.objects.filter(user=self.user).count() == 2

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_register_merge_cart(self):
        session = self.client.session
        Cart.objects.create(session_key=session.session_key, product_id=1)

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
        user = User.objects.filter(name="realName", nick_name="nickName", email="test@mail.com",
                                   is_customer=True).first()
        assert user is not None
        assert Cart.objects.filter(product_id=1, session_key=session.session_key, user=user).exists()

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_cart_product_remove_with_login(self):
        Cart.objects.create(id=1, user_id=1, product_id=1)

        url = '/api/cart_product_remove'
        data = {
            "productId": 1
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 200
        assert not Cart.objects.filter(user=self.user, product_id=1).exists()

    @debugger_queries
    def test_test_ezpay(self):
        Order.objects.create(id=1, user=self.user, merchant_order_no="MSM20211201000001", amount=1000, paid_by="")
        url = '/api/test_ezpay'
        data = {
            "order_id": 1
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data=data, format="json")
        print(response.data)