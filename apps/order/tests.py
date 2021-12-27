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

from .views import add_keyIV_and_encrypt_with_SHA256, AESCipher, encrypt_with_SHA256
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

        result = add_keyIV_and_encrypt_with_SHA256(result)
        print(result)

    @override_settings(DEBUG=True)
    def test_SHA256(self):
        data = "HashKey=12345678901234567890123456789012&ff91c8aa01379e4de621a44e5f11f72e4d25bdb1a18242db6cef9ef07d80b0165e476fd1d9acaa53170272c82d122961e1a0700a7427cfa1cf90db7f6d6593bbc93102a4d4b9b66d9974c13c31a7ab4bba1d4e0790f0cbbbd7ad64c6d3c8012a601ceaa808bff70f94a8efa5a4f984b9d41304ffd879612177c622f75f4214fa&HashIV=1234567890123456"
        result = encrypt_with_SHA256(data)
        print(result)
        assert result == "EA0A6CC37F40C1EA5692E7CBB8AE097653DF3E91365E6A9CD7E91312413C7BB8"

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_order_create(self):
        today_str = timezone.now().strftime("%Y%m%d")
        merchant_order_no = "MSM{}{:06d}".format(today_str, 1)
        Order.objects.create(user=self.user, merchant_order_no=merchant_order_no, amount=Decimal("1000"))

        Cart.objects.create(id=1, user_id=1, product_id=1)
        Cart.objects.create(id=2, user_id=1, product_id=2)

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
        assert int(order.merchant_order_no[3:]) == int(merchant_order_no[3:]) + 1

        order_product_ids = [product.id for product in order.products.all()]
        self.assertEqual(Counter(order_product_ids), Counter([1, 2]))
        assert not Cart.objects.filter(id__in=[1, 2], user_id=1).exists()

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_order_list(self):
        today_str = timezone.now().strftime("%Y%m%d")
        merchant_order_no = "MSM{}{:06d}".format(today_str, 1)
        Order.objects.create(user=self.user, merchant_order_no=merchant_order_no, amount=Decimal("1000"), status=1)

        merchant_order_no = "MSM{}{:06d}".format(today_str, 2)
        Order.objects.create(user=self.user, merchant_order_no=merchant_order_no, amount=Decimal("100"), status=2)

        url = '/api/orders'
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url)
        assert response.status_code == 200
        print(response.data)

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
    def test_test_ezpay_get_post_data(self):
        post_data = {
            'RespondType': 'JSON',
            'Version': '1.4',
            'TimeStamp': '1444963784',  # 請以  time()  格式
            'TransNum': '',
            'MerchantOrderNo': '201409170000001',
            'BuyerName': '王大品',
            'BuyerUBN': '54352706',
            'BuyerAddress': '台北市南港區南港路二段97號8樓',
            'BuyerEmail': '54352706@pay2go.com',
            'Category': 'B2B',
            'TaxType': '1',
            'TaxRate': '5',
            'Amt': '490',
            'TaxAmt': '10',
            'TotalAmt': '500',
            'CarrierType': '',
            'CarrierNum': '',
            'LoveCode': '',
            'PrintFlag': 'Y',
            'ItemName': '商品一|商品二',  # 多項商品時，以「 | 」分開
            'ItemCount': '1|2',  # 多項商品時，以「 | 」分開
            'ItemUnit': '個|個',  # 多項商品時，以「 | 」分開
            'ItemPrice': '300|100',  # 多項商品時，以「 | 」分開
            'ItemAmt': '300|200',  # 多項商品時，以「 | 」分開
            'Comment': '備註',
            'CreateStatusTime': '',
            'Status': '1'  # 1 = 立即開立，0 = 待開立，3 = 延遲開立
        }
        post_data = urlencode(post_data)
        print(post_data)
        expect_urlcode = "RespondType=JSON&Version=1.4&TimeStamp=1444963784&TransNum=" \
                         "&MerchantOrderNo=201409170000001&BuyerName=%E7%8E%8B%E5%A4%A7%E5%93%81" \
                         "&BuyerUBN=54352706&BuyerAddress=%E5%8F%B0%E5%8C%97%E5%B8%82" \
                         "%E5%8D%97%E6%B8%AF%E5%8D%80%E5%8D%97%E6%B8%AF%E8%B7%AF" \
                         "%E4%BA%8C%E6%AE%B597%E8%99%9F8%E6%A8%93&BuyerEmail=54352706%40pay2go.com" \
                         "&Category=B2B&TaxType=1&TaxRate=5&Amt=490&TaxAmt=10" \
                         "&TotalAmt=500&CarrierType=&CarrierNum=&LoveCode=&PrintFlag=Y&ItemName=%" \
                         "E5%95%86%E5%93%81%E4%B8%80%7C%E5%95%86%E5%93%81%E4%BA%8C" \
                         "&ItemCount=1%7C2&ItemUnit=%E5%80%8B%7C%E5%80%8B&ItemPrice=300%7C100" \
                         "&ItemAmt=300%7C200&Comment=%E5%82%99%E8%A8%BB&CreateStatusTime=&Status=1"
        self.assertEqual(post_data, expect_urlcode)

        aes = AESCipher(key='abcdefghijklmnopqrstuvwxyzabcdef', iv='1234567891234567')
        encrypted_post_data = aes.encrypt(raw=post_data)
        expect_encrypted_post_data = "70a61189d7dc0f6abefe7643da144af543470ddf87b1de14ae20cf104f730" \
                                      "dee3f872d15ec141795895ca901e04b59bd691657557d884265e2c817b8db15b5563c" \
                                      "846c88d228bec7d4c9aa57b9d3e5e22c73573e1dc4393c0057185920920fcf17438ec9" \
                                      "4c82de1b109594283c3df21dfc2e3d10a7748d5c9e2f0272e6ff34df191bb517a9736718" \
                                      "33c52dd4a67b27a166f371488a3adc973f0277020dd528353ae88ae1dda9f88f0474f48" \
                                      "e452d5a2e68f41e5c8033937dbb72607003610095b7c0717250e4c8c3611f699fceaa6f" \
                                      "d88a687cc7b3ac5edff3a3a11ac7d040755c7f8c1725011645ea139ceb355e309b4bee9" \
                                      "5a8c37cf9b2f2027b1b7943bc5a946f5879416b2ddf45dd2f4163fe3d995bd189f3053a3" \
                                      "91463565d3f1e284056c21d031554f7d28ed2d674ff62c24b0e93943e20ddd6bf79e6d5" \
                                      "19fc03c590a70f40b2d559ced5a8cd0c1de0d4154112c2fe881c2f352369c23ef2a68cd" \
                                      "eacea72d38c4349484793a93dbbf66078ac533a868cb7378c61c47b79a6c756a3aa484" \
                                      "5006f97bb97ab43a43e17d512c65d2681ed5dd00ef4e0fe76c50f4c093452ee32bc34da" \
                                      "df31cb1d3c562d8d2149506aaa4f2d764ea8e189635aa61863155bec033a5fbeba58a4" \
                                      "63f1f3fc29184fbb85012f339fb57fe96a513ea64cb5b96b7989a2ede6a6a9c164bd1706" \
                                      "52f433688b435e8dcf5246890f2fb9a38fbfe67ed92150d939a690cacb5f3618a7e1234b" \
                                      "efad329e69e56da113cc2889e8ecc2bee9cd4c31eeb44f35817f4b2580510cf6b24189d" \
                                      "f119f07f8f6940e5cd24c23d3bc350975a20a51cd8e8a26254cb25a805929b84bc1bf16" \
                                      "143ed4fb6c3875607ba7089889e24ab662469997cec4cb7f6cd1502eded8cd9ab50380" \
                                      "305b71e1fa57c4".encode("utf-8")

        self.assertEqual(encrypted_post_data, expect_encrypted_post_data)

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

    @debugger_queries
    def test_test_cookie(self):
        url = '/api/cart_product_add'
        data = {
            "productId": 1
        }
        response = self.client.post(url, data=data, format="json")

        url = '/api/test_cookie'
        response = self.client.get(url)
        print(response.data)
        assert response.data["sessionid"] is not None