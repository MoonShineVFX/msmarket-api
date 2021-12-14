from django.utils import timezone
import json

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
    def __init__(self, key=settings.NEWEBPAY_HASHKEY, blk_sz=32):
        self.key = key
        self.blk_sz = blk_sz

    def encrypt(self, raw):
        # raw is the main value
        if raw is None or len(raw) == 0:
            raise NameError("No value given to encrypt")
        raw = raw + '\0' * (self.blk_sz - len(raw) % self.blk_sz)
        raw = raw.encode('utf8mb4')
        # Initialization vector to avoid same encrypt for same strings.

        cipher = AES.new(self.key.encode('utf8mb4'), AES.MODE_CBC, hash_iv.encode('utf8mb4'))
        return base64.b64encode(cipher.encrypt(raw)).decode('utf8mb4')

    def decrypt(self, enc):
        # enc is the encrypted value
        if enc is None or len(enc) == 0:
            raise NameError("No value given to decrypt")
        enc = base64.b64decode(enc)
        # AES.MODE_CFB that allows bigger length or latin values
        cipher = AES.new(self.key.encode('utf8mb4'), AES.MODE_CBC, hash_iv.encode('utf8mb4'))
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
            "Email": order.creator.email,
            "LoginType": 0,
            # --------------------------
            # 將要選擇的付款服務加上參數，目前僅接受信用卡一次付清、ATM轉帳
            "CREDIT": 1,
            "VACC": 1,
            # 即時付款完成後，以 form post 方式要導回的頁面
            "ReturnURL": "商品訂單頁面",
            # 訂單完成後，以背景 post 回報訂單狀況
            "NotifyURL": "處理訂單的網址",
        }
        return urlencode(trade_info_dict)

    def post(self, request, *args, **kwargs):
        today = timezone.now().date()
        ids = self.request.data.get('productIds', [])
        products = Product.objects.filter(id__in=ids)

        # 取得流水號 "MerchantOrderNo" ex: MSM20211201000001
        last_order = Order.objects.filter(created_at__date=today).last()
        if last_order:
            serial_number = last_order.merchant_order_no[3:]
            merchant_order_no = "{}{}".format("MSM", serial_number + 1)
        else:
            today_str = timezone.now().strftime("%Y%m%d")
            merchant_order_no = "MSM{}{:06d}".format(today_str, 1)

        sum_price = sum([product.price for product in products])
        order = Order.objects.create(
            creator=request.user, merchant_order_no=merchant_order_no, amount=sum_price)
        order.products.set(products)

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