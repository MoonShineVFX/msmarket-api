# Generated by Django 3.2.7 on 2022-02-08 09:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0012_add_invoice_counter_and_invoice_merchant_order_no'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invoiceerror',
            name='order',
        ),
    ]
