# Generated by Django 3.2.7 on 2022-04-01 06:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('index', '0011_add_translation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tutorial',
            name='link',
            field=models.TextField(null=True),
        ),
    ]
