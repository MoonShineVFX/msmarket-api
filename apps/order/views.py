from django.utils import timezone
import requests
from decimal import Decimal


from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, CreateAPIView
from ..shortcuts import PostDestroyView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from .models import Cart, Order, NewebpayPayment
from ..product.models import Product
from . import serializers

import base64, re
import hashlib
import codecs
from django.conf import settings
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from urllib.parse import urlencode


# make utf8mb4 recognizable.
codecs.register(lambda name: codecs.lookup('utf8') if name == 'utf8mb4' else None)


hash_key = settings.NEWEBPAY_HASHKEY
hash_iv = settings.NEWEBPAY_HASHIV


class AESCipher:
    def __init__(self, key=hash_key, iv=hash_iv, blk_sz=32):
        self.key = key
        self.iv = iv
        self.blk_sz = blk_sz

    def encrypt(self, raw):
        # raw is the main value
        if raw is None or len(raw) == 0:
            raise NameError("No value given to encrypt")
        raw = raw + '\0' * (self.blk_sz - len(raw) % self.blk_sz)
        raw = raw.encode('utf8mb4')
        # Initialization vector to avoid same encrypt for same strings.

        cipher = AES.new(self.key.encode('utf8mb4'), AES.MODE_CBC, self.iv.encode('utf8mb4'))
        return base64.b64encode(cipher.encrypt(raw)).decode('utf8mb4')

    def decrypt(self, enc):
        # enc is the encrypted value
        if enc is None or len(enc) == 0:
            raise NameError("No value given to decrypt")
        enc = base64.b64decode(enc)
        # AES.MODE_CFB that allows bigger length or latin values
        cipher = AES.new(self.key.encode('utf8mb4'), AES.MODE_CBC, self.iv.encode('utf8mb4'))
        return re.sub(b'\x00*$', b'', cipher.decrypt(enc)).decode('utf8mb4')


def encrypt_with_SHA256(data=None):
    # AES 加密字串前後加上商店專屬加密 HashKey 與商店專屬加密 HashIV
    encrypted_data = "HashKey=%s&%s&HashIV=%s" % (hash_key, data, hash_iv)

    # 將串聯後的字串用 SHA256 壓碼後轉大寫
    result = hashlib.sha256(encrypted_data.encode('utf8mb4')).hexdigest()
    result = result.upper()

    return result


class OrderCreate(APIView):
    permission_classes = (IsAuthenticated, )

    def get_trade_info_query_string(self, order):
        trade_info_dict = {
            # 這些是藍新在傳送參數時的必填欄位
            "MerchantID": settings.NEWEBPAY_ID,
            "MerchantOrderNo": order.merchant_order_no,
            "TimeStamp": timezone.now().timestamp(),
            "RespondType": "JSON",
            "Amt": order.amount,  # 訂單金額
            "Version": "1.6",
            "ItemDesc": "第一次串接就成功！",
            "Email": order.user.email,
            "LoginType": 0,
            # --------------------------
            # 將要選擇的付款服務加上參數，目前僅接受信用卡一次付清、ATM轉帳
            "CREDIT": 1,
            "VACC": 1,
            # 即時付款完成後，以 form post 方式要導回的頁面
            "ReturnURL": "商品訂單頁面",
            # 訂單完成後，以背景 post 回報訂單狀況
            "NotifyURL": "{}/api/newebpay_payment_notify".format(settings.API_HOST),
        }
        return urlencode(trade_info_dict)

    def post(self, request, *args, **kwargs):
        today = timezone.now().date()
        cart_ids = self.request.data.get('cartIds', [])
        carts = Cart.objects.select_related("product").filter(id__in=cart_ids, user=request.user)

        products = [cart.product for cart in carts]
        sum_price = sum([cart.product.price for cart in carts])

        # 取得流水號 "MerchantOrderNo" ex: MSM20211201000001
        last_order = Order.objects.filter(created_at__date=today).last()
        if last_order:
            serial_number = last_order.merchant_order_no[3:]
            merchant_order_no = "{}{}".format("MSM", serial_number + 1)
        else:
            today_str = timezone.now().strftime("%Y%m%d")
            merchant_order_no = "MSM{}{:06d}".format(today_str, 1)

        order = Order.objects.create(
            user=request.user, merchant_order_no=merchant_order_no, amount=sum_price)
        order.products.set(products)

        # 清除購物車已下單商品
        Cart.objects.filter(id__in=cart_ids, user=request.user).delete()

        trade_info = self.get_trade_info_query_string(order=order)
        encrypted_trade_info = AESCipher().encrypt(raw=trade_info)
        trade_sha = encrypt_with_SHA256(data=encrypted_trade_info)

        payment_request_data = {
            "MerchantID": settings.NEWEBPAY_ID,
            "TradeInfo": encrypted_trade_info,
            "TradeSha": trade_sha,  # TradeInfo 經 AES 加密後再 SHA256 加密,
            "Version": "1.6",
        }
        return Response(data=payment_request_data, status=status.HTTP_200_OK)


class NewebpayPaymentNotify(CreateAPIView):
    serializer_class = serializers.NewebpayResponseSerializer


class CartProductList(ListAPIView):
    serializer_class = serializers.CartProductListSerializer

    def post(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = {
            "list": serializer.data,
            "amount": sum(item["price"] for item in serializer.data)
        }
        return Response(data, status=status.HTTP_200_OK)

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Cart.objects.select_related("product").filter(user=self.request.user)
        else:
            if not self.request.session.session_key:
                self.request.session.save()
            session_key = self.request.session.session_key
            return Cart.objects.select_related("product").filter(session_key=session_key)


class CartProductAdd(CreateAPIView):
    serializer_class = serializers.CartAddSerializer

    def perform_create(self, serializer):
        product_id = serializer.validated_data['product_id']
        if self.request.user.is_authenticated:
            if not Cart.objects.filter(product_id=product_id, user=self.request.user).exists():
                return serializer.save(user=self.request.user)
        else:
            if not self.request.session.session_key:
                self.request.session.save()
            session_key = self.request.session.session_key
            if not Cart.objects.filter(product_id=product_id, session_key=session_key).exists():
                return serializer.save(session_key=session_key)


class CartProductRemove(PostDestroyView):
    def get_object(self):
        return get_object_or_404(Cart, product_id=self.request.data.get('productId', None), user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_200_OK)


class TestEZPay(APIView):
    permission_classes = (IsAuthenticated, )

    api_url = "https://cinv.pay2go.com/Api/invoice_issue"

    def get_post_data(self, order):
        if order.products.all() is not None:
            item_count = ""
            item_price = ""
            for p in order.products.all():
                item_count = item_count + "|1" if item_count == "" else "1"

                price = p.price * Decimal("1.05")
                item_price = item_price + "|{}".format(price) if item_price == "" else str(price)
        else:
            item_count = "1"
            item_price = order.amount

        post_data = {
            "RespondType": "JSON",
            "Version": "1.4",
            "TimeStamp": timezone.now().timestamp(),
            "MerchantOrderNo": order.merchant_order_no,
            "Status": "1",
            "Category": "B2C",     # B2B, B2C
            "BuyerName": order.user.name,
            "PrintFlag": "Y",
            "TaxType": "1",
            "TaxRate": 5,
            "Amt": order.amount,  # 發票銷售額(未稅)
            "TaxAmt": 0,
            "TotalAmt": order.amount * Decimal("1.05"),  # 發票總金額(含稅)
            "ItemName": "夢想模型(共{}筆)".format(item_count),
            "ItemCount": item_count,
            "ItemUnit": "組",
            "ItemPrice": item_price,
            "ItemAmt": item_price,
        }
        return urlencode(post_data)

    def post(self, request, *args, **kwargs):
        order_id = self.request.data.get('order_id', None)
        order = get_object_or_404(Order, id=order_id)

        post_data = self.get_post_data(order)
        aes = AESCipher(key=settings.EZPAY_HASHKEY, iv=settings.EZPAY_HASHIV)
        encrypted_post_data = aes.encrypt(raw=post_data)

        data = {
            "MerchantID_": settings.EZPAY_ID,
            "PostData_": encrypted_post_data
        }
        response = requests.post('https://cinv.pay2go.com/Api/invoice_issue', data=data, timeout=3)
        print(response.json())
        return Response(response.json(), status=status.HTTP_200_OK)


class TestCookie(APIView):
    def get(self, request):
        data = {
            "sessionid": self.request.session.session_key
        }
        return Response(data, status=status.HTTP_200_OK)
