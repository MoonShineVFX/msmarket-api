from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient

from ..user.models import User
from .models import LangConfig

from django.test.utils import override_settings
from ..shortcuts import debugger_queries


class LangTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create(id=2, name="admin", email="admin@mail.com", is_staff=True)
        self.user = User.objects.create(id=1, name="user01", email="user01@mail.com")
        LangConfig.objects.create(lang="zh", menu_store="商店", text_signin="登入",
                                  product_detail_format_and_renderer="軟體格式與算圖引擎",
                                  product_detail_notice_message="購買後，可以在我的模型庫下載其他檔案格式")
        LangConfig.objects.create(lang="en", menu_store="menu_store", text_signin="text_signin",
                                  product_detail_format_and_renderer="product_detail_format_and_renderer",
                                  product_detail_notice_message="product_detail_notice_message")

    @override_settings(DEBUG=True)
    @debugger_queries
    def test_lang_configs(self):
        url = '/api/lang_configs'
        response = self.client.post(url)
        print(response.data)
        assert response.status_code == 200

    @override_settings(DEBUG=True)
    @debugger_queries
    def admin_lang_config_update(self):
        url = '/api/admin_lang_config_update'
        data = {
            "zh": {
                "menu_store": "商店",
                "text_signin": "登入",
                "product_detail_format_and_renderer": "軟體格式與算圖引擎",
                "product_detail_notice_message": "購買後，可以在我的模型庫下載其他檔案格式",
                "wrong_config": "1234d86f47s68dfs6546d5486zf4g"
            },
            "en": {
                "menu_store": "Store",
                "text_signin": "Sign",
                "product_detail_format_and_renderer": "Format",
                "product_detail_notice_message": ""
            }
        }
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, data=data, format='json')
        print(response.data)
        assert response.status_code == 200
        expect_data = data["zh"]
        expect_data.pop("wrong_config")
        assert LangConfig.objects.filter(**expect_data).exists()

    @override_settings(DEBUG=True)
    @debugger_queries
    def admin_lang_config_search_with_key(self):
        url = '/api/admin_lang_config_search'
        data = {
            "key": "product_detail_",
            #"value": "",
        }
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, data=data, format='json')
        assert response.status_code == 200

        expect = {'zh': {'product_detail_section_title01': None, 'product_detail_section_title02': None,
                         'product_detail_notice_message': '購買後，可以在我的模型庫下載其他檔案格式',
                         'product_detail_format_and_renderer': '軟體格式與算圖引擎'},
                  'en': {'product_detail_section_title01': None, 'product_detail_section_title02': None,
                         'product_detail_notice_message': 'product_detail_notice_message',
                         'product_detail_format_and_renderer': 'product_detail_format_and_renderer'}
                  }
        assert response.data == expect

    @override_settings(DEBUG=True)
    @debugger_queries
    def admin_lang_config_search_with_value(self):
        url = '/api/admin_lang_config_search'
        data = {
            "value": "格式",
        }
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, data=data, format='json')
        assert response.status_code == 200
        print(response.data)
        expect = {'zh': {'product_detail_notice_message': '購買後，可以在我的模型庫下載其他檔案格式',
                         'product_detail_format_and_renderer': '軟體格式與算圖引擎'},
                  'en': {'product_detail_notice_message': 'product_detail_notice_message',
                         'product_detail_format_and_renderer': 'product_detail_format_and_renderer'}}

        assert response.data == expect

    @override_settings(DEBUG=True)
    @debugger_queries
    def admin_lang_config_search_with_key_and_value(self):
        url = '/api/admin_lang_config_search'
        data = {
            "key": "product_detail_notice",
            "value": "格式",
        }
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, data=data, format='json')
        assert response.status_code == 200
        print(response.data)
        expect = {'zh': {'product_detail_notice_message': '購買後，可以在我的模型庫下載其他檔案格式'},
                  'en': {'product_detail_notice_message': 'product_detail_notice_message'}
                  }

        assert response.data == expect

    @override_settings(DEBUG=True)
    @debugger_queries
    def admin_lang_config_search_with_key_and_value_no_result(self):
        url = '/api/admin_lang_config_search'
        data = {
            "key": "product_detail_notice",
            "value": "12312",
        }
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, data=data, format='json')
        assert response.status_code == 200
        print(response.data)
        expect = {'zh': {},
                  'en': {}
                  }

        assert response.data == expect