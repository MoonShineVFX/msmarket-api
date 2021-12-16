# Generated by Django 3.2.7 on 2021-11-08 11:18

import apps.product.models
import apps.storage
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='model_size',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='product',
            name='price',
            field=models.DecimalField(decimal_places=4, default=0, max_digits=10),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='image',
            name='file',
            field=models.ImageField(storage=apps.storage.PublicGoogleCloudStorage, upload_to=apps.product.models.get_directory_path),
        ),
        migrations.AlterField(
            model_name='image',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='product.product'),
        ),
        migrations.AlterField(
            model_name='price',
            name='price',
            field=models.DecimalField(decimal_places=4, max_digits=10),
        ),
        migrations.AlterField(
            model_name='price',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prices', to='product.product'),
        ),
        migrations.AlterField(
            model_name='product',
            name='preview',
            field=models.ImageField(storage=apps.storage.PublicGoogleCloudStorage, upload_to=apps.product.models.get_directory_path),
        ),
    ]