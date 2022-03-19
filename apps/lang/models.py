from django.db import models


class LangConfig(models.Model):
    lang = models.CharField(max_length=2)
    updated_at = models.DateTimeField(null=True)

    # common
    og_title = models.CharField(max_length=100,  null=True, blank=True)
    og_description = models.CharField(max_length=100,  null=True, blank=True)
    text_logo = models.CharField(max_length=100,  null=True, blank=True)
    text_logout = models.CharField(max_length=100,  null=True, blank=True)
    menu_store = models.CharField(max_length=100,  null=True, blank=True)
    menu_about = models.CharField(max_length=100,  null=True, blank=True)
    menu_tutorial = models.CharField(max_length=100,  null=True, blank=True)
    btn_submit = models.CharField(max_length=100,  null=True, blank=True)
    btn_show_more = models.CharField(max_length=100,  null=True, blank=True)
    btn_cancel = models.CharField(max_length=100,  null=True, blank=True)
    btn_confirm = models.CharField(max_length=100,  null=True, blank=True)
    btn_verify = models.CharField(max_length=100,  null=True, blank=True)

    # 語系、幣別
    currency_tw = models.CharField(max_length=100,  null=True, blank=True)
    currency_en = models.CharField(max_length=100,  null=True, blank=True)
    lang_zh = models.CharField(max_length=100,  null=True, blank=True)
    lang_en = models.CharField(max_length=100,  null=True, blank=True)
    lang_cn = models.CharField(max_length=100,  null=True, blank=True)
    lang_jp = models.CharField(max_length=100,  null=True, blank=True)

    # footer
    text_privacy = models.CharField(max_length=100,  null=True, blank=True)
    text_custom_service = models.CharField(max_length=100,  null=True, blank=True)

    # 錯誤訊息
    error_required = models.CharField(max_length=100,  null=True, blank=True)
    error_pattern = models.CharField(max_length=100,  null=True, blank=True)
    error_password_different = models.CharField(max_length=100,  null=True, blank=True)
    error_password_at_least_eight = models.CharField(max_length=100,  null=True, blank=True)

    # 首頁
    home_title = models.CharField(max_length=100,  null=True, blank=True)
    home_section_title01 = models.CharField(max_length=100,  null=True, blank=True)
    home_section_title02 = models.CharField(max_length=100,  null=True, blank=True)

    # 關於
    about_title = models.CharField(max_length=100,  null=True, blank=True)
    about_support_model = models.CharField(max_length=100,  null=True, blank=True)
    about_support_software = models.CharField(max_length=100,  null=True, blank=True)
    about_support_render = models.CharField(max_length=100,  null=True, blank=True)

    # 文件
    tutorial_title = models.CharField(max_length=100,  null=True, blank=True)

    # 隱私權
    privacy_title = models.CharField(max_length=100,  null=True, blank=True)

    # 訪客頁: 登入、註冊、忘記密碼、重設密碼、帳號啟用
    text_signin = models.CharField(max_length=100,  null=True, blank=True)
    text_signin_title = models.CharField(max_length=100,  null=True, blank=True)
    text_account = models.CharField(max_length=100,  null=True, blank=True)
    text_password = models.CharField(max_length=100,  null=True, blank=True)
    text_signin_with_google = models.CharField(max_length=100,  null=True, blank=True)
    text_forgot_password = models.CharField(max_length=100,  null=True, blank=True)
    text_register = models.CharField(max_length=100,  null=True, blank=True)
    text_nickname = models.CharField(max_length=100,  null=True, blank=True)
    text_real_name = models.CharField(max_length=100,  null=True, blank=True)
    text_enter_password = models.CharField(max_length=100,  null=True, blank=True)
    text_confirm_password = models.CharField(max_length=100,  null=True, blank=True)
    text_agree_privacy = models.CharField(max_length=100,  null=True, blank=True)
    btn_return_to_signin = models.CharField(max_length=100,  null=True, blank=True)
    text_enter_register_email = models.CharField(max_length=100,  null=True, blank=True)
    btn_get_reset_password_link = models.CharField(max_length=100,  null=True, blank=True)
    text_reset_password = models.CharField(max_length=100,  null=True, blank=True)
    text_new_password = models.CharField(max_length=100,  null=True, blank=True)
    text_new_password_success = models.CharField(max_length=100,  null=True, blank=True)
    text_email_sent = models.CharField(max_length=100,  null=True, blank=True)
    text_register_success_message = models.CharField(max_length=100,  null=True, blank=True)
    text_active_account_title = models.CharField(max_length=100,  null=True, blank=True)
    text_active_account_message = models.CharField(max_length=100,  null=True, blank=True)

    btn_confirm_order = models.CharField(max_length=100,  null=True, blank=True)
    cart_box_title = models.CharField(max_length=100,  null=True, blank=True)
    cart_go_to_checkout = models.CharField(max_length=100,  null=True, blank=True)
    cart_order_title = models.CharField(max_length=100,  null=True, blank=True)
    cart_section_title = models.CharField(max_length=100,  null=True, blank=True)
    cart_text_notice = models.CharField(max_length=100,  null=True, blank=True)
    cart_text_empty = models.CharField(max_length=100,  null=True, blank=True)

    btn_add_to_cart = models.CharField(max_length=100,  null=True, blank=True)
    product_no_data = models.CharField(max_length=100,  null=True, blank=True)
    product_select_label = models.CharField(max_length=100,  null=True, blank=True)
    product_detail_section_title01 = models.CharField(max_length=100,  null=True, blank=True)
    product_detail_section_title02 = models.CharField(max_length=100,  null=True, blank=True)
    product_detail_notice_message = models.CharField(max_length=100,  null=True, blank=True)
    product_detail_format_and_renderer = models.CharField(max_length=100,  null=True, blank=True)
    product_format = models.CharField(max_length=100,  null=True, blank=True)
    product_render = models.CharField(max_length=100,  null=True, blank=True)
    product_file_size = models.CharField(max_length=100,  null=True, blank=True)
    product_download = models.CharField(max_length=100,  null=True, blank=True)
    product_model_sum = models.CharField(max_length=100,  null=True, blank=True)
    product_per_image_size = models.CharField(max_length=100,  null=True, blank=True)

    member_my_account = models.CharField(max_length=100,  null=True, blank=True)
    member_account_center = models.CharField(max_length=100,  null=True, blank=True)
    member_my_product = models.CharField(max_length=100,  null=True, blank=True)
    member_account_update = models.CharField(max_length=100,  null=True, blank=True)
    member_old_password = models.CharField(max_length=100,  null=True, blank=True)
    member_change_password = models.CharField(max_length=100,  null=True, blank=True)
    member_change_password_success = models.CharField(max_length=100,  null=True, blank=True)
    member_mobile_download_notice = models.CharField(max_length=100,  null=True, blank=True)
    text_return_to_account = models.CharField(max_length=100,  null=True, blank=True)
    btn_saved = models.CharField(max_length=100,  null=True, blank=True)

    order_text_order_record = models.CharField(max_length=100,  null=True, blank=True)
    order_status_unpaid = models.CharField(max_length=100,  null=True, blank=True)
    order_status_success = models.CharField(max_length=100,  null=True, blank=True)
    order_status_fail = models.CharField(max_length=100,  null=True, blank=True)
    order_status_cancel = models.CharField(max_length=100,  null=True, blank=True)
    order_text_order_number = models.CharField(max_length=100,  null=True, blank=True)
    order_text_create_at = models.CharField(max_length=100,  null=True, blank=True)
    order_text_paid_at = models.CharField(max_length=100,  null=True, blank=True)
    order_text_status = models.CharField(max_length=100,  null=True, blank=True)
    order_text_quantity = models.CharField(max_length=100,  null=True, blank=True)
    order_text_total_price = models.CharField(max_length=100,  null=True, blank=True)
    order_text_payment = models.CharField(max_length=100,  null=True, blank=True)
    order_text_invoice = models.CharField(max_length=100,  null=True, blank=True)
    order_payment_CREDIT = models.CharField(max_length=100,  null=True, blank=True)
    order_payment_VACC = models.CharField(max_length=100,  null=True, blank=True)
    order_detail = models.CharField(max_length=100,  null=True, blank=True)
    order_success = models.CharField(max_length=100,  null=True, blank=True)

