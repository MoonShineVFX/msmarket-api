# Generated by Django 3.2.7 on 2022-05-17 11:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('index', '0013_add_banner_product_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='tutorial',
            name='active_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='tutorial',
            name='inactive_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='tutorial',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
    ]
