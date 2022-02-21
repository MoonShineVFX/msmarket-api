# Generated by Django 3.2.7 on 2022-02-16 09:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0013_remove_InvoiceError_order_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newebpaypayment',
            name='encrypted_data',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='decrypted_payment', to='order.newebpayresponse'),
        ),
    ]