# Generated by Django 3.2.7 on 2021-12-29 09:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('index', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='tutorial',
            old_name='website',
            new_name='link',
        ),
    ]