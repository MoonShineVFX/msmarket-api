# Generated by Django 3.2.7 on 2022-01-03 09:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_add_user_is_customer_flag'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='is_customer',
        ),
        migrations.AddField(
            model_name='user',
            name='is_staff',
            field=models.BooleanField(default=False),
        ),
    ]