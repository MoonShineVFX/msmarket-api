# Generated by Django 3.2.7 on 2021-12-09 07:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('product', '0003_move_tags_to_product'),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(null=True)),
                ('status', models.IntegerField()),
                ('paid_at', models.DateTimeField(null=True)),
                ('paid_by', models.CharField(max_length=10)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_order_creation', to=settings.AUTH_USER_MODEL)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='product.product')),
                ('updater', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='order_order_update', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='NewebpayPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(max_length=10)),
                ('message', models.CharField(max_length=50)),
                ('amount', models.DecimalField(decimal_places=4, max_digits=10)),
                ('trade_no', models.CharField(max_length=20)),
                ('payment_type', models.CharField(max_length=10)),
                ('pay_time', models.DateTimeField()),
                ('ip', models.CharField(max_length=15)),
                ('EscrowBank', models.CharField(blank=True, max_length=10, null=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='order.order')),
            ],
        ),
    ]