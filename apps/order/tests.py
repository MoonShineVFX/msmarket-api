import json
from django.utils import timezone
from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from django.test.utils import override_settings
from ..shortcuts import debugger_queries
from .models import Order
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
    def test_web_order_create(self):
        url = '/api/web_order_create'
        data = {
            "productIds": [1, 2]
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url)
        print(response.data)
        assert response.status_code == 200

