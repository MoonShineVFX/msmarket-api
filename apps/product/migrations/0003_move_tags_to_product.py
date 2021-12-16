# Generated by Django 3.2.7 on 2021-11-09 08:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('category', '0001_initial'),
        ('product', '0002_add_price'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='model',
            name='tags',
        ),
        migrations.AddField(
            model_name='product',
            name='tags',
            field=models.ManyToManyField(to='category.Tag'),
        ),
    ]