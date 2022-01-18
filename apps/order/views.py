from django.utils import timezone
import requests
from decimal import Decimal
from django.db import transaction

from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, CreateAPIView, GenericAPIView
from ..shortcuts import PostDestroyView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404, get_list_or_404
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from .models import Cart, Order, NewebpayPayment, NewebpayResponse
from ..product.models import Product
from . import serializers


import hashlib
import codecs
from django.conf import settings
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from urllib.parse import urlencode, parse_qs
from binascii import hexlify

# make utf8mb4 recognizable.
codecs.register(lambda name: codecs.lookup('utf8') if name == 'utf8mb4' else None)


hash_key = settings.NEWEBPAY_HASHKEY
hash_iv = settings.NEWEBPAY_HASHIV

today = timezone.now().date()


class AESCipher:
    def __init__(self, key, iv, block_size=32):
        self.key = key.encode('utf8mb4')
        self.iv = iv.encode('utf8mb4')
        self.block_size = block_size
        self.cipher = AES.new(self.key, AES.MODE_CBC, self.iv)

    def encrypt(self, raw):
        if type(raw) == str:
            raw = raw.encode('utf8mb4')
        encrypted_text = self.cipher.encrypt(pad(raw, AES.block_size))
        return hexlify(encrypted_text)

    def decrypt(self, enc):
        enc = codecs.decode(enc, "hex")
        plaintext = unpad(self.cipher.decrypt(enc), AES.block_size)
        return eval(plaintext.decode('utf8mb4'))


newepay_cipher = AESCipher(key=hash_key, iv=hash_iv)
ezpay_cipher = AESCipher(key=settings.EZPAY_HASHKEY, iv=settings.EZPAY_HASHIV)


def encrypt_with_SHA256(data=None):
    result = hashlib.sha256(data.encode('utf8mb4')).hexdigest()
    result = result.upper()
    return result


def add_keyIV_and_encrypt_with_SHA256(data=None):
    # AES 加密字串前後加上商店專屬加密 HashKey 與商店專屬加密 HashIV
    if type(data) == bytes:
        data = data.decode("utf-8")
    data = "HashKey=%s&%s&HashIV=%s" % (hash_key, data, hash_iv)
    # 將串聯後的字串用 SHA256 壓碼後轉大寫
    result = encrypt_with_SHA256(data)

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
            "Amt": int(order.amount),  # 訂單金額
            "Version": "1.6",
            "ItemDesc": "第一次串接就成功！",
            "Email": order.user.email,
            "LoginType": 0,
            # --------------------------
            # 將要選擇的付款服務加上參數，目前僅接受信用卡一次付清、ATM轉帳
            "CREDIT": 1,
            "VACC": 1,
            # 即時付款完成後，以 form post 方式要導回的頁面
            #"ReturnURL": "https://{}/payment_result?no={}".format(settings.API_HOST, order.merchant_order_no),
            # 訂單完成後，以背景 post 回報訂單狀況
            "NotifyURL": "https://{}/api/newebpay_payment_notify".format(settings.API_HOST),
        }
        return urlencode(trade_info_dict)

    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        cart_ids = self.request.data.get('cartIds', [])
        carts = get_list_or_404(Cart.objects.select_related("product"), id__in=cart_ids, user=request.user)

        products = [cart.product for cart in carts]
        sum_price = sum([cart.product.price for cart in carts])

        # 取得流水號 "MerchantOrderNo" ex: MSM20211201000001
        last_order = Order.objects.filter(created_at__date=today).last()
        if last_order:
            serial_number = int(last_order.merchant_order_no[3:])
            merchant_order_no = "{}{}".format("MSM", serial_number + 1)
        else:
            today_str = timezone.now().strftime("%Y%m%d")
            merchant_order_no = "MSM{}{:06d}".format(today_str, 1)

        order = Order.objects.create(
            user=request.user, merchant_order_no=merchant_order_no, amount=sum_price, item_count=len(products))
        order.products.set(products)

        # 清除購物車已下單商品
        Cart.objects.filter(id__in=cart_ids, user=request.user).delete()

        trade_info = self.get_trade_info_query_string(order=order)
        encrypted_trade_info = newepay_cipher.encrypt(raw=trade_info)
        trade_sha = add_keyIV_and_encrypt_with_SHA256(data=encrypted_trade_info)

        payment_request_data = {
            "MerchantID": settings.NEWEBPAY_ID,
            "TradeInfo": encrypted_trade_info,
            "TradeSha": trade_sha,  # TradeInfo 經 AES 加密後再 SHA256 加密,
            "Version": "1.6",
        }
        return Response(data=payment_request_data, status=status.HTTP_200_OK)


class OrderList(GenericAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = serializers.OrderSerializer

    def get(self, request, *args, **kwargs):
        return self.post(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = {
            "list": serializer.data,
        }
        return Response(data, status=status.HTTP_200_OK)

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class OrderDetail(GenericAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = serializers.OrderDetailSerializer
    queryset = Order.objects.prefetch_related("products")

    def get(self, request, order_number, *args, **kwargs):
        order = get_object_or_404(self.queryset, merchant_order_no=order_number)
        serializer = self.serializer_class(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminOrderSearch(GenericAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def post(self, request, *args, **kwargs):
        serializer = serializers.AdminOrderSearchParamsSerializer(data=self.request.data)
        if serializer.is_valid():
            orders = Order.objects.select_related("user")

            merchant_order_no = serializer.data.get('orderNumber', None)
            email = serializer.data.get('account', None)
            invoice_number = serializer.data.get('invoice', None)
            start_date = serializer.data.get('startDate', None)
            end_date = serializer.data.get('endDate', None)

            if merchant_order_no:
                orders = orders.filter(merchant_order_no__icontains=merchant_order_no)
            if email:
                orders = orders.filter(user__email__icontains=email)
            if invoice_number:
                orders = orders.filter(invoice_number__icontains=invoice_number)
            if start_date:
                orders = orders.filter(created_at__date__gte=start_date)
            if end_date:
                orders = orders.filter(created_at__date__lte=end_date)

            data = {
                "list": serializers.AdminOrderListSerializer(orders, many=True).data,
            }
            return Response(data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminOrderList(OrderList):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminOrderListSerializer

    def get_queryset(self):
        return Order.objects.select_related("user").all()


class AdminOrderDetail(OrderDetail):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminOrderDetailSerializer
    queryset = Order.objects.select_related("user").prefetch_related("products")


class NewebpayPaymentNotify(CreateAPIView):
    serializer_class = serializers.NewebpayResponseSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        trade_info = serializer.validated_data["TradeInfo"]
        trade_sha = serializer.validated_data["TradeSha"]
        trade_status = serializer.validated_data["Status"]

        if add_keyIV_and_encrypt_with_SHA256(trade_info) != trade_sha:
            error = "Wrong trade_sha"
        elif NewebpayResponse.objects.filter(created_at__date=today, TradeSha=trade_sha).exists():
            error = "NewebpayResponse already exists"
        else:
            decrypt_trade_info, is_decrypted = self.decrypt_trade_info(encrypted_trade_info=trade_info)
            result = decrypt_trade_info["Result"]
            merchant_order_no = result.get("MerchantOrderNo", None)
            order = Order.objects.filter(merchant_order_no=merchant_order_no).first()

            # 紀錄 Newebpay response
            encrypted_data = serializer.save(**{
                "is_decrypted": is_decrypted,
                "order_id": order.id if order else None
            })

            # 解碼並存成 payment
            payment = None
            payment_serializer = serializers.NewebpayPaymentSerializer(data=result)

            if payment_serializer.is_valid():
                payment = payment_serializer.save(**{
                    "status": decrypt_trade_info["Status"],
                    "message": decrypt_trade_info["Message"],
                    "order_id": order.id if order else None,
                    "encrypted_data_id": encrypted_data.id
                })

            # 交易成功時，更新 order
            if trade_status == "SUCCESS":
                order_update = {"status": Order.SUCCESS}

                if payment:
                    order_update.update({
                        "paid_at": payment.pay_time,
                        "paid_by": payment.payment_type,
                        "success_payment": payment.id
                    })
            else:
                order_update = {"status": Order.FAIL}
            Order.objects.filter(id=order.id).update(**order_update)

            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)
        return Response(error, status=status.HTTP_400_BAD_REQUEST)

    def decrypt_trade_info(self, encrypted_trade_info):
        decrypted_trade_info = newepay_cipher.decrypt(enc=encrypted_trade_info)
        if "Status" in decrypted_trade_info:
            result = decrypted_trade_info
            return result, True
        else:
            return None, False


class CartProductList(GenericAPIView):
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

    def post(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        carts = Cart.objects.filter(user=self.request.user)
        serializer = serializers.CartProductListSerializer(carts, many=True)
        data = {
            "list": serializer.data,
        }
        return Response(data=data, status=status.HTTP_200_OK)


class TestEZPay(APIView):
    permission_classes = (IsAuthenticated, )

    api_url = "https://cinv.pay2go.com/Api/invoice_issue"

    def get_post_data(self, order):
        if len(order.products.all()) > 0:
            item_count = ""
            item_price = ""
            for p in order.products.all():
                item_count = item_count + "|1" if item_count == "" else "1"

                price = p.price * Decimal("1.05")
                item_price = item_price + "|{}".format(price) if item_price == "" else str(price)
        else:
            item_count = "1"
            item_price = int(order.amount)

        tax_rate = Decimal("0.05")
        tax_amt = order.amount * tax_rate

        post_data = {
            "RespondType": "JSON",
            "Version": "1.4",
            "TimeStamp": int(timezone.now().timestamp()),
            "MerchantOrderNo": order.merchant_order_no,
            "Status": "1",
            "Category": "B2C",     # B2B, B2C
            "BuyerName": order.user.name,
            "PrintFlag": "Y",
            "TaxType": "1",
            "TaxRate": 5,
            "Amt": int(order.amount),  # 發票銷售額(未稅)
            "TaxAmt": int(tax_amt),
            "TotalAmt": int(order.amount + tax_amt),  # 發票總金額(含稅)
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
        encrypted_post_data = ezpay_cipher.encrypt(raw=post_data)

        data = {
            "MerchantID_": settings.EZPAY_ID,
            "PostData_": encrypted_post_data
        }
        response = requests.post('https://cinv.pay2go.com/Api/invoice_issue', data=data, timeout=3)

        return Response(response.json(), status=status.HTTP_200_OK)


class TestCookie(APIView):
    def get(self, request):
        data = {
            "sessionid": self.request.session.session_key
        }
        return Response(data, status=status.HTTP_200_OK)
