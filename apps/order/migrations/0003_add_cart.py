# Generated by Django 3.2.7 on 2021-12-14 08:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('product', '0003_move_tags_to_product'),
        ('order', '0002_change_order_products_to_m2m'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='creator',
        ),
        migrations.RemoveField(
            model_name='order',
            name='updated_at',
        ),
        migrations.RemoveField(
            model_name='order',
            name='updater',
        ),
        migrations.AddField(
            model_name='order',
            name='user',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, related_name='orders', to='user.user'),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(max_length=40, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='product.product')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='carts', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]