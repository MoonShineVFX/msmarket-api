# Generated by Django 3.2.7 on 2022-06-16 09:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0011_add_user_real_name_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_verified',
            field=models.BooleanField(default=False),
        ),
    ]
