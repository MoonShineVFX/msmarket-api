# Generated by Django 3.2.7 on 2022-02-07 06:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('index', '0006_add_banner_update_params'),
    ]

    operations = [
        migrations.AddField(
            model_name='banner',
            name='active_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='banner',
            name='inactive_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='banner',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
    ]
