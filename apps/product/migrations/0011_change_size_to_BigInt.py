# Generated by Django 3.2.7 on 2022-01-27 09:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0010_change_model_size_model_count_default_0'),
    ]

    operations = [
        migrations.AlterField(
            model_name='model',
            name='size',
            field=models.BigIntegerField(),
        ),
        migrations.AlterField(
            model_name='product',
            name='model_size',
            field=models.BigIntegerField(default=0),
        ),
    ]
