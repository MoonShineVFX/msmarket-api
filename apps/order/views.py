#!/usr/bin/python
# -*- coding: utf-8 -*-

import io
import xlsxwriter
import json
import calendar
import datetime
from django.utils import timezone
import requests
from decimal import Decimal
from django.db import transaction

from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, CreateAPIView, GenericAPIView
from ..shortcuts import PostDestroyView, SwitchLangMixin, PostCreateView, PostUpdateView
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404, get_list_or_404
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from ..authentications import AdminJWTAuthentication, CustomerJWTAuthentication

from .models import Cart, Order, NewebpayPayment, NewebpayResponse, EInvoice, InvoiceError, PaperInvoice
from ..product.models import Product
from ..user.models import CustomerProduct
from . import serializers


import hashlib
import codecs
from django.conf import settings
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from urllib.parse import urlencode, parse_qsl
from binascii import hexlify

# make utf8mb4 recognizable.
codecs.register(lambda name: codecs.lookup('utf8') if name == 'utf8mb4' else None)


hash_key = settings.NEWEBPAY_HASHKEY
hash_iv = settings.NEWEBPAY_HASHIV


class AESCipher:
    def __init__(self, key=hash_key, iv=hash_iv, block_size=32):
        self.key = key.encode('utf8mb4')
        self.iv = iv.encode('utf8mb4')
        self.block_size = block_size

    def encrypt(self, raw):
        if type(raw) == str:
            raw = raw.encode('utf8mb4')
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        encrypted_text = cipher.encrypt(pad(raw, self.block_size))
        return hexlify(encrypted_text)

    def decrypt(self, enc):
        enc = codecs.decode(enc, "hex")
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        plaintext = unpad(cipher.decrypt(enc), self.block_size)
        return plaintext.decode('utf8mb4')


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


class EZPayInvoiceMixin(object):
    api_url = "https://cinv.pay2go.com/Api/invoice_issue"

    def get_post_data(self, order):
        if len(order.products.all()) > 1:
            item_name = None
            item_count = None
            item_unit = None
            item_price = None
            for p in order.products.all():
                item_name = item_name + "|" + p.title[:30] if item_name else p.title[:30]
                item_count = item_count + "|1" if item_count else "1"
                item_unit = item_unit + "|組" if item_unit else "組"
                price = int(p.price * Decimal("1.05"))
                item_price = item_price + "|{}".format(price) if item_price else str(price)
        else:
            item_name = order.products.all()[0].title[:30] if order.products.all() else ""
            item_count = "1"
            item_unit = "組"
            item_price = int(order.amount)

        tax_rate = Decimal("0.05")
        tax_amt = order.amount * tax_rate

        post_data = {
            "RespondType": "String",
            "Version": "1.4",
            "TimeStamp": int(timezone.now().timestamp()),
            "MerchantOrderNo": '%s%03d' % (order.merchant_order_no, order.invoice_counter),
            "Status": "1",
            "Category": "B2C",  # B2B, B2C
            "BuyerName": order.user.name,
            "PrintFlag": "Y",
            "TaxType": "1",
            "TaxRate": 5,
            "Amt": int(order.amount),  # 發票銷售額(未稅)
            "TaxAmt": int(tax_amt),
            "TotalAmt": int(order.amount + tax_amt),  # 發票總金額(含稅)
            "ItemName": item_name,
            "ItemCount": item_count,
            "ItemUnit": item_unit,
            "ItemPrice": item_price,
            "ItemAmt": item_price,
        }
        return urlencode(post_data)

    def call_e_invoice_api_and_save(self, order):
        """
        save invoice or invoice_error, set order params without save
        """
        if order.invoice_number:
            return
        post_data = self.get_post_data(order)
        encrypted_post_data = ezpay_cipher.encrypt(raw=post_data)

        data = {
            "MerchantID_": settings.EZPAY_ID,
            "PostData_": encrypted_post_data
        }

        response = requests.post('https://cinv.pay2go.com/Api/invoice_issue', data=data, timeout=3)
        self.handle_str_response(data=response.text, order=order)
        return response.text

    def handle_str_response(self, data, order):
        if type(data) == str:
            if data[0:7] == "Status=":
                data = dict(parse_qsl(data))
            else:
                data = json.loads(data)

        result_serializer = serializers.EZPayResponseSerializer(data=data)
        if result_serializer.is_valid():
            validated_data = result_serializer.validated_data
            if validated_data["status"] == "SUCCESS":
                invoice_serializer = serializers.EZPayInvoiceSerializer(data=data)
                invoice_serializer.is_valid()
                e_invoice_data = invoice_serializer.validated_data

                invoice_number = e_invoice_data.get("invoice_number")
                ezpay_id = e_invoice_data.pop('merchant_id')

                invoice_merchant_order_no = e_invoice_data.get('invoice_merchant_order_no')
                merchant_order_no = invoice_merchant_order_no[:-3]

                # 商店代號正確，才會建立新發票
                if ezpay_id == settings.EZPAY_ID and order.merchant_order_no == merchant_order_no:
                    e_invoice_data["payment_id"] = order.success_payment_id if order else None
                    e_invoice = EInvoice.objects.create(**e_invoice_data)

                    order.invoice_number = invoice_number
                    order.e_invoice = e_invoice
            else:
                invoice_error = InvoiceError.objects.create(**validated_data)
                order.invoice_counter = order.invoice_counter + 1
        else:
            print(result_serializer.errors)


class NewebpayMixin(object):
    version = "2.0"

    def get_trade_info_query_string(self, order):
        trade_info_dict = {
            # 這些是藍新在傳送參數時的必填欄位
            "MerchantID": settings.NEWEBPAY_ID,
            "MerchantOrderNo": order.merchant_order_no,
            "TimeStamp": order.created_at,
            "RespondType": "JSON",
            "Amt": int(order.amount),  # 訂單金額
            "Version": self.version,
            "ItemDesc": "第一次串接就成功！",
            "Email": order.user.email,
            "LoginType": 0,
            # --------------------------
            # 將要選擇的付款服務加上參數，目前僅接受信用卡一次付清、ATM轉帳
            "CREDIT": 1,
            "VACC": 1,
            # 即時付款完成後，以 form post 方式要導回的頁面
            "ReturnURL": "https://{}/order/payment_result?no={}".format(settings.API_HOST, order.merchant_order_no),
            # 訂單完成後，以背景 post 回報訂單狀況
            "NotifyURL": "https://{}/api/newebpay_payment_notify".format(settings.API_HOST),
        }
        return urlencode(trade_info_dict)

    def get_newebpay_payment_request_data(self, order):
        trade_info = self.get_trade_info_query_string(order=order)
        encrypted_trade_info = newepay_cipher.encrypt(raw=trade_info)
        trade_sha = add_keyIV_and_encrypt_with_SHA256(data=encrypted_trade_info)

        payment_request_data = {
            "MerchantID": settings.NEWEBPAY_ID,
            "TradeInfo": encrypted_trade_info,
            "TradeSha": trade_sha,  # TradeInfo 經 AES 加密後再 SHA256 加密,
            "Version": self.version,
        }
        return payment_request_data


class OrderCreate(APIView, NewebpayMixin):
    authentication_classes = [CustomerJWTAuthentication]
    permission_classes = (IsAuthenticated, )

    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        cart_ids = self.request.data.get('cartIds', [])
        carts = get_list_or_404(Cart.objects.select_related("product"), id__in=cart_ids, user=request.user)

        products = [cart.product for cart in carts]
        product_ids = [cart.product_id for cart in carts]
        sum_price = sum([cart.product.price for cart in carts])

        serializer = serializers.OrderCreateSerializer(data=self.request.data)
        serializer.is_valid()
        invoice_type = serializer.validated_data["invoice_type"]
        bought_product_ids = CustomerProduct.objects.values_list("id", flat=True).filter(user_id=request.user.id, product_id__in=product_ids).all()

        if bought_product_ids:
            return Response({"boughtProductIds": list(bought_product_ids)}, status=status.HTTP_400_BAD_REQUEST)

        if len(product_ids) != len(set(product_ids)):
            return Response("There are same products in cart, you have to remove it first.", status=status.HTTP_400_BAD_REQUEST)

        # 取得流水號 "MerchantOrderNo" ex: MSM20211201000001
        last_order = Order.objects.filter(created_at__date=timezone.now().date()).last()
        if last_order:
            serial_number = int(last_order.merchant_order_no[3:])
            merchant_order_no = "{}{}".format("MSM", serial_number + 1)
        else:
            today_str = timezone.now().strftime("%Y%m%d")
            merchant_order_no = "MSM{}{:06d}".format(today_str, 1)

        order_data = {
            "user": request.user,
            "merchant_order_no": merchant_order_no,
            "amount": sum_price,
            "item_count": len(products)

        }
        # 建立紙本發票
        if invoice_type == "paper":
            paper_invoice = serializer.save()
            order_data["paper_invoice_id"] = paper_invoice.id
            order_data["invoice_type"] = paper_invoice.id

        # 建立訂單
        order = Order.objects.create(**order_data)
        order.products.set(products)

        # 清除購物車已下單商品
        Cart.objects.filter(id__in=cart_ids, user=request.user).delete()

        payment_request_data = self.get_newebpay_payment_request_data(order=order)
        return Response(data=payment_request_data, status=status.HTTP_200_OK)


class GetNewebpayDataFromOrder(APIView, NewebpayMixin):
    authentication_classes = [CustomerJWTAuthentication]
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        order_id = self.request.data.get('id', None)
        order = get_object_or_404(Order, id=order_id, user_id=self.request.user.id)

        payment_request_data = self.get_newebpay_payment_request_data(order=order)
        return Response(data=payment_request_data, status=status.HTTP_200_OK)


class OrderList(GenericAPIView):
    authentication_classes = [CustomerJWTAuthentication]
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
        return Order.objects.filter(user=self.request.user).order_by("-created_at")


class OrderDetail(GenericAPIView, SwitchLangMixin):
    authentication_classes = [CustomerJWTAuthentication]
    permission_classes = (IsAuthenticated, )
    serializer_class = serializers.OrderDetailSerializer
    queryset = Order.objects.prefetch_related("products")

    def get(self, request, order_number, *args, **kwargs):
        self.set_language()
        order = get_object_or_404(self.queryset, merchant_order_no=order_number)
        serializer = self.serializer_class(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminOrderSearch(GenericAPIView):
    authentication_classes = [AdminJWTAuthentication]
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
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminOrderListSerializer

    def get_queryset(self):
        return Order.objects.select_related("user").order_by('-created_at').all()


class AdminOrderDetail(OrderDetail):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = serializers.AdminOrderDetailSerializer
    queryset = Order.objects.select_related("user", "paper_invoice").prefetch_related("products")


class NewebpayPaymentNotify(GenericAPIView, EZPayInvoiceMixin):
    serializer_class = serializers.NewebpayResponseSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        trade_info = serializer.validated_data["TradeInfo"]
        trade_sha = serializer.validated_data["TradeSha"]
        trade_status = serializer.validated_data["Status"]

        if add_keyIV_and_encrypt_with_SHA256(trade_info) != trade_sha:
            error = "Wrong trade_sha"
        elif NewebpayResponse.objects.filter(TradeSha=trade_sha).exists():
            error = "NewebpayResponse already exists"
        else:
            # 紀錄 Newebpay response
            encrypted_data = NewebpayResponse(**serializer.validated_data)

            decrypt_trade_info, is_decrypted = self.decrypt_trade_info(encrypted_trade_info=trade_info)

            result = decrypt_trade_info["Result"]
            merchant_order_no = result.get("MerchantOrderNo", None)
            order = Order.objects.select_related("user").prefetch_related("products").filter(
                merchant_order_no=merchant_order_no).first()

            # 解碼並存成 payment
            payment = None
            payment_serializer = serializers.NewebpayPaymentSerializer(data=result)

            if payment_serializer.is_valid():
                encrypted_data.is_decrypted = is_decrypted
                encrypted_data.order_id = order.id if order else None
                encrypted_data.save()

                payment = payment_serializer.save(**{
                    "status": decrypt_trade_info["Status"],
                    "message": decrypt_trade_info["Message"],
                    "order_id": order.id if order else None,
                    "encrypted_data_id": encrypted_data.id
                })
            else:
                encrypted_data.save()

            # 交易成功時，更新 order 狀態，新增已購買商品，呼叫發票api
            if trade_status == "SUCCESS":
                order.status = Order.SUCCESS
                customer_products = [
                    CustomerProduct(
                        user_id=order.user_id, product_id=product.id, order_id=order.id
                     ) for product in order.products.all()
                ]
                CustomerProduct.objects.bulk_create(customer_products)

                if payment:
                    order.paid_at = payment.pay_time
                    order.paid_by = payment.payment_type
                    order.success_payment_id = payment.id

                    # 新增電子發票 不會存order
                    if order.invoice_type == 0 and not order.invoice_number:
                        self.call_e_invoice_api_and_save(order=order)

            else:
                order.status = Order.FAIL
            # order更新部份一次儲存
            order.save()

            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(error, status=status.HTTP_400_BAD_REQUEST)

    def decrypt_trade_info(self, encrypted_trade_info):
        decrypted_trade_info = newepay_cipher.decrypt(enc=encrypted_trade_info)
        if "Status" in decrypted_trade_info:
            result = json.loads(decrypted_trade_info)
            return result, True
        else:
            return None, False


class CartProductList(GenericAPIView, SwitchLangMixin):
    authentication_classes = [CustomerJWTAuthentication]
    serializer_class = serializers.CartProductListSerializer

    def post(self, request, *args, **kwargs):
        self.set_language()
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
    authentication_classes = [CustomerJWTAuthentication]
    serializer_class = serializers.CartAddSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product_id = serializer.validated_data['product_id']

        if self.request.user.is_authenticated:
            if (Cart.objects.filter(product_id=product_id, user=self.request.user).exists()
                    or CustomerProduct.objects.filter(product_id=product_id, user=self.request.user).exists()):
                return Response({"productId": "The product is already bought or in the cart."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                save_data = {"user": self.request.user}
        else:
            if not self.request.session.session_key:
                self.request.session.save()
            session_key = self.request.session.session_key
            if Cart.objects.filter(product_id=product_id, session_key=session_key).exists():
                return Response({"productId": "The product is already in the cart."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                save_data = {"session_key": session_key}

        serializer.save(**save_data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CartProductRemove(PostDestroyView):
    authentication_classes = [CustomerJWTAuthentication]

    def get_object(self):
        return get_object_or_404(Cart, id=self.request.data.get('cartId', None), user=self.request.user)

    def post(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        carts = Cart.objects.filter(user=self.request.user)
        serializer = serializers.CartProductListSerializer(carts, many=True)
        data = {
            "amount": sum(item["price"] for item in serializer.data),
            "list": serializer.data,
        }
        return Response(data=data, status=status.HTTP_200_OK)


class CreateEZPayInvoiceFromOrder(APIView, EZPayInvoiceMixin):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)

    def post(self, request, *args, **kwargs):
        order_id = self.request.data.get('orderId', None)

        order = get_object_or_404(Order, id=order_id)
        result = self.call_e_invoice_api_and_save(order=order)
        order.save()
        return Response(result, status=status.HTTP_200_OK)


class AdminOrderPaperInvoiceUpdate(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)

    def post(self, request, *args, **kwargs):
        serializer = serializers.AdminOrderPaperInvoiceSerializer(data=self.request.data)
        serializer.is_valid()
        order_id = serializer.validated_data.get('id')
        invoice_number = serializer.validated_data.get('invoice_number')
        order = get_object_or_404(Order, id=order_id)
        Order.objects.filter(id=order_id).update(invoice_number=invoice_number)
        PaperInvoice.objects.filter(id=order.paper_invoice_id).update(invoice_number=invoice_number)
        return Response(self.request.data, status=status.HTTP_200_OK)


class AdminOrderExport(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)

    def report_response(self, start, end):
        first_day = datetime.datetime(int(start[:4]), int(start[-2:]), 1)
        last_year = int(end[:4])
        last_month = int(end[-2:])
        last_day = datetime.datetime(last_year, last_month, calendar.monthrange(last_year, last_month)[1])

        filename = "MoonshineMarket3D_orders_{}_{}.xls".format(start, end)

        order_list = Order.objects.values_list(
            "id", "merchant_order_no", "user__email", "amount", "status", "created_at", "paid_at", "paid_by",
            "success_payment__trade_no", "invoice_number", "paper_invoice__real_name", "paper_invoice__address",
            "paper_invoice__receiver_name", "paper_invoice__receiver_address", "invoice_type", "paper_invoice__type",
            "paper_invoice__company_name", "paper_invoice__tax_number",
        ).filter(created_at__gte=first_day, created_at__lte=last_day).order_by("id")

        title = ["ID", "訂單編號", "會員帳號", "金額", "訂單狀態", "訂單成立時間", "付款時間", "付款方式",
                 "交易序號", "發票號碼", "訂購人", "訂購人地址",
                 "收件人", "收件地址", "發票類型", "紙本發票類型",
                 "公司名稱", "統一編號"]

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True, 'remove_timezone': True})
        worksheet = workbook.add_worksheet('orders')

        for col_num, data in enumerate(title):
            worksheet.write(0, col_num, data)

        for row_num, data in enumerate(order_list):
            worksheet.write_row(1 + row_num, 0, data)

        workbook.close()
        output.seek(0)

        response = HttpResponse(
            output,
            content_type='application/vnd.ms-excel'
        )
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
        return response

    def get(self, request, *args, **kwargs):
        start = self.request.query_params.get("start", None)
        end = self.request.query_params.get("end", None)
        if start and end:
            response = self.report_response(start, end)
            return response
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        start = self.request.data.get("start", None)
        end = self.request.data.get("end", None)
        if start and end:
            response = self.report_response(start, end)
            return response
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class TestCookie(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = (IsAuthenticated, IsAdminUser)
    def get(self, request):
        data = {
            "sessionid": self.request.session.session_key
        }
        return Response(data, status=status.HTTP_200_OK)
