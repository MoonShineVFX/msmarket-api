# Generated by Django 3.2.7 on 2021-12-28 12:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0006_order_add_item_count'),
    ]

    operations = [
        migrations.RenameField(
            model_name='newebpaypayment',
            old_name='EscrowBank',
            new_name='escrow_bank',
        ),
    ]