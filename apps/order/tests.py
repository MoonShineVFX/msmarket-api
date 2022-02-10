#!/usr/bin/python
# -*- coding: utf-8 -*-

import base64
import json
from unittest import mock
from collections import OrderedDict, Counter
from django.utils import timezone
from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from django.test.utils import override_settings
from ..shortcuts import debugger_queries
from .models import Order, Cart, NewebpayResponse, NewebpayPayment, Invoice, InvoiceError
from ..product.models import Product
from ..user.models import User, CustomerProduct

from .views import add_keyIV_and_encrypt_with_SHA256, AESCipher, encrypt_with_SHA256, EZPayInvoiceMixin
from urllib.parse import urlencode

test_hash_key = 'eb0HEQAJFJyevSKM5zSP9F7jwPhTA5Bz'
test_hash_iv = 'CXTiuqCetQm232OP'


class OrderTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(id=1, name="user01", email="user01@mail.com")
        self.admin = User.objects.create(id=2, name="admin", email="admin@mail.com", is_staff=True)

        p1 = Product.objects.create(id=1, title="product01", description="", price=Decimal(1), model_size=0,
                                    model_count=4, texture_size="1800x1800", creator_id=1)
        p2 = Product.objects.create(id=2, title="product02", description="", price=Decimal(1), model_size=0,
                                    model_count=4, texture_size="1800x1800", creator_id=1)

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

    def test_encrypt_with_AES_example(self):
        trade_info = {
            'MerchantID': 3430112,
            'RespondType': 'JSON',
            'TimeStamp': 1485232229,
            'Version': 1.4,
            'MerchantOrderNo': 'S_1485232229',
            'Amt': 40,
            'ItemDesc': 'UnitTest'
        }
        key = '12345678901234567890123456789012'
        iv = '1234567890123456'

        trade_info = urlencode(trade_info)
        c = AESCipher(key=key, iv=iv)
        ciphertext = c.encrypt(raw=trade_info)

        result = "HashKey=%s&%s&HashIV=%s" % (key, ciphertext.decode("utf-8"), iv)
        result = encrypt_with_SHA256(result)

        assert result == "EA0A6CC37F40C1EA5692E7CBB8AE097653DF3E91365E6A9CD7E91312413C7BB8"

        print(ciphertext)
        result = c.decrypt(enc=ciphertext)
        print(result)

    def test_SHA256(self):
        data = "HashKey=12345678901234567890123456789012&ff91c8aa01379e4de621a44e5f11f72e4d25bdb1a18242db6cef9ef07d80b0165e476fd1d9acaa53170272c82d122961e1a0700a7427cfa1cf90db7f6d6593bbc93102a4d4b9b66d9974c13c31a7ab4bba1d4e0790f0cbbbd7ad64c6d3c8012a601ceaa808bff70f94a8efa5a4f984b9d41304ffd879612177c622f75f4214fa&HashIV=1234567890123456"
        result = encrypt_with_SHA256(data)

        assert result == "EA0A6CC37F40C1EA5692E7CBB8AE097653DF3E91365E6A9CD7E91312413C7BB8"

    @mock.patch('apps.order.views.hash_key', test_hash_key)
    @mock.patch('apps.order.views.hash_iv', test_hash_iv)
    def test_response_TradeInfo_TradeSha_correct(self):
        data = "c6f1fdd8595c20ba221ad3eb2e19d5aae4e50f96f99b4e271aff2f2839bafb70a372819b90dec91f1d9e9980499d657150237e99fe6bd3d40e74742ddb578191d7e1cd8cabf06a8d951d7eb59d75342aa2e4e592924f9e9c98765d866e8433fd71c7f75faa9344e232cef4fc234a8fd09a2fee72170452305d2390a6a0f1d7c817a337bf90d21b22f6f98d21750e3f63f31c1c13f3bad65ff6788ecb2ada43150462bded77ee74e870ee5d91e7ee943b97abfc26ab39983cc69d01ce827ad65fa4f6a87edc58f6ac5f3eb3470d17925365120a1b90e577f37ba2fd88786c8c34883aa9d79eb5d294fa8f45b0db809d053d5f9b09754df05e3f8ad58398c11232b9afd58b0d5287d68490457f25a8064d640f096f5fe4bbfd84a25d136bbd8e2789379c7db89ba7e380f807bdf17553b52cdd47cd9eb758f58feb0922721fa1bf05e96401dd88d12a79dc7c9ebdcc0b157b532b666bed08790daf8741eaad12d9c00087bc6349c968b8830d4d40bdeed52e3bb1bc6e86ebab14ba99b7e84d90d56dc97c014465b40970ff97e40839da2061e645a3f2d6fe4cdee829b46095992cbfcebc1f4e2cd533c1e915a063a38eea600e3c4d2a5f6ba0b5af4042f52fe25a5cac049674762aff60d9d9cc196ddbca3f746697f69ffd554071d06a85e9e14b"
        result = add_keyIV_and_encrypt_with_SHA256(data)
        print(result)
        assert result == "FF915DC66673057BC7B94804A4E5A23C1829CC0EEBB52D46ADC70E0FE1AFD01C"

    def test_decrypt_TradeInfo_example(self):
        ciphertext = "ff91c8aa01379e4de621a44e5f11f72e4d25bdb1a18242db6cef9ef07d80b0165e476fd1d9acaa53170272c82d122961e1a0700a7427cfa1cf90db7f6d6593bbc93102a4d4b9b66d9974c13c31a7ab4bba1d4e0790f0cbbbd7ad64c6d3c8012a601ceaa808bff70f94a8efa5a4f984b9d41304ffd879612177c622f75f4214fa"
        key = '12345678901234567890123456789012'
        iv = '1234567890123456'
        c = AESCipher(key=key, iv=iv)
        result = c.decrypt(enc=ciphertext)
        assert result == "MerchantID=3430112&RespondType=JSON&TimeStamp=1485232229&Version=1.4&MerchantOrderNo=S_1485232229&Amt=40&ItemDesc=UnitTest"

    def test_decrypt_TradeInfo(self):
        ciphertext = "c6f1fdd8595c20ba221ad3eb2e19d5aae4e50f96f99b4e271aff2f2839bafb70a372819b90dec91f1d9e9980499d657150237e99fe6bd3d40e74742ddb578191d7e1cd8cabf06a8d951d7eb59d75342aa2e4e592924f9e9c98765d866e8433fd71c7f75faa9344e232cef4fc234a8fd09a2fee72170452305d2390a6a0f1d7c817a337bf90d21b22f6f98d21750e3f63f31c1c13f3bad65ff6788ecb2ada43150462bded77ee74e870ee5d91e7ee943b97abfc26ab39983cc69d01ce827ad65fa4f6a87edc58f6ac5f3eb3470d17925365120a1b90e577f37ba2fd88786c8c34883aa9d79eb5d294fa8f45b0db809d053d5f9b09754df05e3f8ad58398c11232b9afd58b0d5287d68490457f25a8064d640f096f5fe4bbfd84a25d136bbd8e2789379c7db89ba7e380f807bdf17553b52cdd47cd9eb758f58feb0922721fa1bf05e96401dd88d12a79dc7c9ebdcc0b157b532b666bed08790daf8741eaad12d9c00087bc6349c968b8830d4d40bdeed52e3bb1bc6e86ebab14ba99b7e84d90d56dc97c014465b40970ff97e40839da2061e645a3f2d6fe4cdee829b46095992cbfcebc1f4e2cd533c1e915a063a38eea600e3c4d2a5f6ba0b5af4042f52fe25a5cac049674762aff60d9d9cc196ddbca3f746697f69ffd554071d06a85e9e14b"
        c = AESCipher(key=test_hash_key, iv=test_hash_iv)
        result = c.decrypt(enc=ciphertext)
        result = json.loads(result)
        expect = {"Status": "SUCCESS", "Message": "\u6388\u6b0a\u6210\u529f",
                          "Result": {"MerchantID": "MS326698321", "Amt": 100, "TradeNo": "21122717471292431",
                                     "MerchantOrderNo": "MSM20211227000013", "RespondType": "JSON",
                                     "IP": "203.69.143.113", "EscrowBank": "HNCB", "PaymentType": "CREDIT",
                                     "RespondCode": "00", "Auth": "025171", "Card6No": "400022", "Card4No": "1111",
                                     "Exp": "2703", "TokenUseStatus": "0", "InstFirst": 0, "InstEach": 0, "Inst": 0,
                                     "ECI": "", "PayTime": "2021-12-27 17:47:12", "PaymentMethod": "CREDIT"}}
        self.assertEqual(result["Result"], expect["Result"])

    @mock.patch('apps.order.views.hash_key', test_hash_key)
    @mock.patch('apps.order.views.hash_iv', test_hash_iv)
    def test_response_TradeInfo_TradeSha_error(self):
        data = "c23138942d393501963a0c89a5999de3ef910c1c3ba1f4aa28ef69853797bf9b5fc7ea30bb84587c4207d15feb1c250ce95175441b15873113ed121e17dbc9d78826c08aa37fbe495cb44cb6e45968ba5c13001b2c55e34fb7337de3e7be90fb9ce0278b72014f0b1cf7c831288d1e5672d51c10b7887232813079d3433e1b2c34522428ad066e96c735127183f13a60d69d03f93b51c9b75eba64a021f70f3d9ade4ba72090844e0cef45eb17b59e9b7420cb20d3da8645998ed53d2a1f483a15632d3c9c9c64ce252caacde0ac27cdb43700da1fb2b983a7c0a5ca87e2b6cd2541c3e432d26aab94f5427bc653efd30d9832a51d09266f3a8423ca70b6159c7b31a98257aa74d19ae66b5d0b35486e602382c310a954c2d409706d66c6f6864c105539a0c4811f9fe649e24f35a6a8f9cd52f6ca68722935622b3aa0c15f01b5e2528ddf460201c1c7ef98b67fabf0e42dc40bac04a117bb59dc374b5dbffbb449f86723cb374116e8e0840ed4a80e607f510e3b4d6adbc0b5a928c4a62fffc09199335f3bcad6c75e2feebae0eea0ae0b9e0895d5f96878ee3923e5ca7d7432c14113e629a838fbe915fed818381f3dca1e4d61d78308b725ba3065e680511e48edf5f083144318bc8d8b67928be7cac5f40e3e0a8a802fdb0e2309b98315"
        result = add_keyIV_and_encrypt_with_SHA256(data)
        print(result)
        assert result == "B18D511BFEB27B1D86B36BFE01B79845864CDFB6AB030DD01555C6BFA4BA5EFE"

    def test_decrypt_TradeInfo_error(self):
        ciphertext = "c23138942d393501963a0c89a5999de3ef910c1c3ba1f4aa28ef69853797bf9b5fc7ea30bb84587c4207d15feb1c250ce95175441b15873113ed121e17dbc9d78826c08aa37fbe495cb44cb6e45968ba5c13001b2c55e34fb7337de3e7be90fb9ce0278b72014f0b1cf7c831288d1e5672d51c10b7887232813079d3433e1b2c34522428ad066e96c735127183f13a60d69d03f93b51c9b75eba64a021f70f3d9ade4ba72090844e0cef45eb17b59e9b7420cb20d3da8645998ed53d2a1f483a15632d3c9c9c64ce252caacde0ac27cdb43700da1fb2b983a7c0a5ca87e2b6cd2541c3e432d26aab94f5427bc653efd30d9832a51d09266f3a8423ca70b6159c7b31a98257aa74d19ae66b5d0b35486e602382c310a954c2d409706d66c6f6864c105539a0c4811f9fe649e24f35a6a8f9cd52f6ca68722935622b3aa0c15f01b5e2528ddf460201c1c7ef98b67fabf0e42dc40bac04a117bb59dc374b5dbffbb449f86723cb374116e8e0840ed4a80e607f510e3b4d6adbc0b5a928c4a62fffc09199335f3bcad6c75e2feebae0eea0ae0b9e0895d5f96878ee3923e5ca7d7432c14113e629a838fbe915fed818381f3dca1e4d61d78308b725ba3065e680511e48edf5f083144318bc8d8b67928be7cac5f40e3e0a8a802fdb0e2309b98315"
        c = AESCipher(key=test_hash_key, iv=test_hash_iv)
        result = c.decrypt(enc=ciphertext)
        result = json.loads(result)
        print(result)

    @mock.patch('apps.order.views.newepay_cipher', AESCipher(key=test_hash_key, iv=test_hash_iv))
    @mock.patch('apps.order.views.hash_key', test_hash_key)
    @mock.patch('apps.order.views.hash_iv', test_hash_iv)
    @override_settings(DEBUG=True)
    @debugger_queries
    def test_newebpay_payment_notify_success(self):
        order = Order.objects.create(user=self.user, merchant_order_no="MSM20211227000013", amount=1000,
                                     invoice_counter=5)
        order.products.set([1])

        url = '/api/newebpay_payment_notify'
        data = {
            "Status": "SUCCESS",
            "MerchantID": "MerchantID",
            "TradeInfo": "c6f1fdd8595c20ba221ad3eb2e19d5aae4e50f96f99b4e271aff2f2839bafb70a372819b90dec91f1d9e9980499d657150237e99fe6bd3d40e74742ddb578191d7e1cd8cabf06a8d951d7eb59d75342aa2e4e592924f9e9c98765d866e8433fd71c7f75faa9344e232cef4fc234a8fd09a2fee72170452305d2390a6a0f1d7c817a337bf90d21b22f6f98d21750e3f63f31c1c13f3bad65ff6788ecb2ada43150462bded77ee74e870ee5d91e7ee943b97abfc26ab39983cc69d01ce827ad65fa4f6a87edc58f6ac5f3eb3470d17925365120a1b90e577f37ba2fd88786c8c34883aa9d79eb5d294fa8f45b0db809d053d5f9b09754df05e3f8ad58398c11232b9afd58b0d5287d68490457f25a8064d640f096f5fe4bbfd84a25d136bbd8e2789379c7db89ba7e380f807bdf17553b52cdd47cd9eb758f58feb0922721fa1bf05e96401dd88d12a79dc7c9ebdcc0b157b532b666bed08790daf8741eaad12d9c00087bc6349c968b8830d4d40bdeed52e3bb1bc6e86ebab14ba99b7e84d90d56dc97c014465b40970ff97e40839da2061e645a3f2d6fe4cdee829b46095992cbfcebc1f4e2cd533c1e915a063a38eea600e3c4d2a5f6ba0b5af4042f52fe25a5cac049674762aff60d9d9cc196ddbca3f746697f69ffd554071d06a85e9e14b",
            "TradeSha": "FF915DC66673057BC7B94804A4E5A23C1829CC0EEBB52D46ADC70E0FE1AFD01C",
            "Version": "1.6"
        }
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 200
        newebpay_response = NewebpayResponse.objects.get(
            order_id=order.id, MerchantID="MerchantID", is_decrypted=True)
        newebpay_payment = NewebpayPayment.objects.get(
            order_id=order.id, payment_type="CREDIT", amount=100, encrypted_data_id=newebpay_response.id)
        assert Order.objects.filter(
            id=order.id, status=Order.SUCCESS, paid_by="CREDIT", success_payment_id=newebpay_payment.id).exists()
        assert CustomerProduct.objects.filter(order_id=order.id, user_id=order.user_id, product_id=1).exists()
        assert Invoice.objects.filter(id=order.id).exists() # test will not pass

    @mock.patch('apps.order.views.newepay_cipher', AESCipher(key=test_hash_key, iv=test_hash_iv))
    @mock.patch('apps.order.views.hash_key', test_hash_key)
    @mock.patch('apps.order.views.hash_iv', test_hash_iv)
    @override_settings(DEBUG=True)
    @debugger_queries
    def test_newebpay_payment_notify_fail(self):
        order = Order.objects.create(user=self.user, merchant_order_no="MSM20211227000013", amount=1000)

        url = '/api/newebpay_payment_notify'
        data = {
            "Status": "MPG01001",
            "MerchantID": "MerchantID",
            "TradeInfo": "c6f1fdd8595c20ba221ad3eb2e19d5aae4e50f96f99b4e271aff2f2839bafb70a372819b90dec91f1d9e9980499d657150237e99fe6bd3d40e74742ddb578191d7e1cd8cabf06a8d951d7eb59d75342aa2e4e592924f9e9c98765d866e8433fd71c7f75faa9344e232cef4fc234a8fd09a2fee72170452305d2390a6a0f1d7c817a337bf90d21b22f6f98d21750e3f63f31c1c13f3bad65ff6788ecb2ada43150462bded77ee74e870ee5d91e7ee943b97abfc26ab39983cc69d01ce827ad65fa4f6a87edc58f6ac5f3eb3470d17925365120a1b90e577f37ba2fd88786c8c34883aa9d79eb5d294fa8f45b0db809d053d5f9b09754df05e3f8ad58398c11232b9afd58b0d5287d68490457f25a8064d640f096f5fe4bbfd84a25d136bbd8e2789379c7db89ba7e380f807bdf17553b52cdd47cd9eb758f58feb0922721fa1bf05e96401dd88d12a79dc7c9ebdcc0b157b532b666bed08790daf8741eaad12d9c00087bc6349c968b8830d4d40bdeed52e3bb1bc6e86ebab14ba99b7e84d90d56dc97c014465b40970ff97e40839da2061e645a3f2d6fe4cdee829b46095992cbfcebc1f4e2cd533c1e915a063a38eea600e3c4d2a5f6ba0b5af4042f52fe25a5cac049674762aff60d9d9cc196ddbca3f746697f69ffd554071d06a85e9e14b",
            "TradeSha": "FF915DC66673057BC7B94804A4E5A23C1829CC0EEBB52D46ADC70E0FE1AFD01C",
            "Version": "1.6"
        }
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 200
        assert NewebpayResponse.objects.filter(order_id=order.id, MerchantID="MerchantID", is_decrypted=True).exists()
        assert NewebpayPayment.objects.filter(order_id=order.id).exists()
        assert Order.objects.filter(id=order.id, status=Order.FAIL).exists()

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
    def test_order_create_with_bought_products(self):
        today_str = timezone.now().strftime("%Y%m%d")
        merchant_order_no = "MSM{}{:06d}".format(today_str, 1)
        order = Order.objects.create(user=self.user, merchant_order_no=merchant_order_no, amount=Decimal("1000"))

        Cart.objects.create(id=1, user_id=1, product_id=1)
        Cart.objects.create(id=2, user_id=1, product_id=2)

        CustomerProduct.objects.create(user=self.user, order=order, product_id=1)
        url = '/api/order_create'
        data = {
            "cartIds": [1, 2]
        }
        self.client.force_authenticate(user=self.user)
        print("test start")
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 400
        assert Cart.objects.filter(id__in=[1, 2], user_id=1).exists()

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
    def test_order_detail(self):
        today_str = timezone.now().strftime("%Y%m%d")
        merchant_order_no = "MSM{}{:06d}".format(today_str, 1)
        order = Order.objects.create(user=self.user, merchant_order_no=merchant_order_no, amount=Decimal("1000"), status=1)
        order.products.set([1, 2])

        url = '/api/orders/{}'.format(merchant_order_no)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        assert response.status_code == 200
        print(response.data)

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_order_list(self):
        today_str = timezone.now().strftime("%Y%m%d")
        merchant_order_no = "MSM{}{:06d}".format(today_str, 1)
        Order.objects.create(user=self.user, merchant_order_no=merchant_order_no, amount=Decimal("1000"), status=1)

        merchant_order_no = "MSM{}{:06d}".format(today_str, 2)
        Order.objects.create(user=self.user, merchant_order_no=merchant_order_no, amount=Decimal("100"), status=2)

        url = '/api/admin_orders'
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url)
        assert response.status_code == 403

        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url)
        assert response.status_code == 200
        print(response.data)

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_order_detail(self):
        today_str = timezone.now().strftime("%Y%m%d")
        merchant_order_no = "MSM{}{:06d}".format(today_str, 1)
        order = Order.objects.create(user=self.user, merchant_order_no=merchant_order_no, amount=Decimal("1000"), status=1)
        order.products.set([1, 2])

        url = '/api/admin_orders/{}'.format(merchant_order_no)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        assert response.status_code == 403

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(url)
        assert response.status_code == 200
        print(response.data)

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_admin_order_search(self):
        today_str = timezone.now().strftime("%Y%m%d")
        merchant_order_no = "MSM{}{:06d}".format(today_str, 1)
        order = Order.objects.create(user=self.user, merchant_order_no=merchant_order_no, amount=Decimal("1000"), status=1)
        order.products.set([1, 2])

        url = '/api/admin_order_search'
        data = {
            "orderNumber": merchant_order_no,
            "account": "",
            "invoice": "",
            "startDate": "2021-01-01",
            "endDate": timezone.now().date().isoformat()
        }
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, data=data, format="json")
        assert response.status_code == 200
        print(response.data)

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
        print(response.data)
        expect = {
            'list': [OrderedDict(
                [('id', 1), ('productId', 1), ('title', 'product01'), ('imgUrl', None), ('price', Decimal('1.0000'))]),
                     OrderedDict([('id', 2), ('productId', 2), ('title', 'product02'), ('imgUrl', None),
                                  ('price', Decimal('1.0000'))])],
            'amount': Decimal('2.0000')
        }
        self.assertEqual(response.data['amount'], Decimal('2.0000'))
        self.assertEqual(len(response.data['list']), 2)
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
        assert response.status_code == 400
        assert Cart.objects.filter(user=self.user, product_id=1).exists()
        assert Cart.objects.filter(user=self.user, product_id=1).count() == 1

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_cart_product_add_bought_product_with_login(self):
        order = Order.objects.create(user=self.user, merchant_order_no="merchant_order_no", amount=Decimal("1000"))
        CustomerProduct.objects.create(user=self.user, order=order, product_id=1)

        url = '/api/cart_product_add'
        data = {
            "productId": 1
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data=data, format="json")
        print(response.data)
        assert response.status_code == 400
        assert not Cart.objects.filter(user=self.user, product_id=1).exists()

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

        assert response.status_code == 400
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
        user = User.objects.filter(name="realName", nick_name="nickName", email="test@mail.com").first()
        assert user is not None
        assert Cart.objects.filter(product_id=1, session_key=session.session_key, user=user).exists()

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_cart_product_remove_with_login(self):
        Cart.objects.create(id=1, user_id=1, product_id=1)
        Cart.objects.create(id=2, user_id=1, product_id=2)

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
        order = Order.objects.create(id=1, user=self.user, merchant_order_no="MSM20211201000001001", amount=1000, paid_by="")
        order.products.set([1, 2])
        result = EZPayInvoiceMixin().get_post_data(order=order)
        print(result)
        print(result.encode('utf-8'))

    @debugger_queries
    def test_test_ezpay_get_post_data_with_one_product(self):
        order = Order.objects.create(id=1, user=self.user, merchant_order_no="MSM20211201000001001", amount=1000, paid_by="")
        order.products.set([1])
        result = EZPayInvoiceMixin().get_post_data(order=order)
        print(result)
        print(result.encode('utf-8'))

    @debugger_queries
    def test_test_ezpay_encrypt(self):
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

    @override_settings(EZPAY_ID="3502275")
    @override_settings(DEBUG=True)
    @debugger_queries
    def test_ezpay_invoice_handle_response_with_error(self):
        order = Order.objects.create(user=self.user, merchant_order_no="MSM20220207000001", amount=1000)
        encrypted_data = NewebpayResponse.objects.create(
            order_id=order.id, Status="", TradeInfo="", TradeSha="", Version="",
            MerchantID="MerchantID", is_decrypted=True)
        payment = NewebpayPayment.objects.create(
            encrypted_data_id=encrypted_data.id, order_id=order.id, amount=1000, pay_time=timezone.now())
        order.success_payment = payment
        order.save()
        data = "Status=LIB10003&Message=%E8%A9%B2%E7%AD%86%E8%87%AA%E8%A8%82%E5%96%AE%E8%99%9F%E5%B7%B2%E9%87%8D%E8%A6%86%E9%96%8B%E7%AB%8B%E7%99%BC%E7%A5%A8%EF%BC%8C%E8%AB%8B%E7%A2%BA%E8%AA%8D"
        EZPayInvoiceMixin().handle_str_response(data=data, order=order)
        assert InvoiceError.objects.filter(status='LIB10003').exists()

    @override_settings(EZPAY_ID="3502275")
    @override_settings(DEBUG=True)
    @debugger_queries
    def test_ezpay_invoice_handle_response_with_str(self):
        order = Order.objects.create(user=self.user, merchant_order_no="MSM20211227000013", amount=1000)
        encrypted_data = NewebpayResponse.objects.create(
            order_id=order.id, Status="", TradeInfo="", TradeSha="", Version="",
            MerchantID="MerchantID", is_decrypted=True)
        payment = NewebpayPayment.objects.create(
            encrypted_data_id=encrypted_data.id, order_id=order.id, amount=1000, pay_time=timezone.now())
        order.success_payment = payment
        order.save()

        data = "Status=SUCCESS&Message=%E9%9B%BB%E5%AD%90%E7%99%BC%E7%A5%A8%E9%96%8B%E7%AB%8B%E6%88%90%E5%8A%9F" \
               "&Result=&CheckCode=2676BC6ADE45247740753A74799224D055D46277E8D32A49B7D5DE77B70D9C6A" \
               "&InvoiceNumber=DS12223164&InvoiceTransNo=15110411233370252&MerchantID=3502275&TotalAmt=365" \
               "&RandomNum=2909&MerchantOrderNo=MSM20211227000013001&CreateTime=2015-11-04+11%3A23%3A33" \
               "&BarCode=10412DS122231642909&QRcodeL=DS12223164104110429090000015c0000016d0478523699005522fqMSCB6cFR" \
               "vu3oUfw2bfgg%3D%3D%3A%2A%2A%2A%2A%2A%2A%2A%2A%2A%2A%3A2%3A2%3A0%3A&QRcodeR=%2A%2A%E5%95%86%E5%93%81%" \
               "E4%B8%80%3A2%3A99%3A%E5%95%86%E5%93%81%E4%BA%8C%3A3%3A50&EndStr=%23%23"
        EZPayInvoiceMixin().handle_str_response(data=data, order=order)
        assert Invoice.objects.filter(
            invoice_number="DS12223164", order_id=order.id, invoice_merchant_order_no="MSM20211227000013001").exists()
        assert Order.objects.filter(id=order.id, invoice_number="DS12223164").exists()

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

    def test_encode_base64(self):
        message = {   "type": "service_account",   "project_id": "ms-model-lib-project-id"}
        message_str = json.dumps(message)
        message_bytes = message_str.encode()
        base64_bytes = base64.b64encode(message_bytes)

        base64_message = base64_bytes.decode()
        print(base64_message)

        # encoded string from first example
        b64_str = base64_message
        b64_str = b64_str.encode()
        b64_bytes = base64.b64decode(b64_str)
        decode_str = b64_bytes.decode()
        decode_dict = json.loads(decode_str)

