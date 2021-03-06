# Generated by Django 3.2.7 on 2022-03-22 08:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('index', '0010_banner_add_mobile_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='aboutus',
            name='description_en',
            field=models.TextField(default='', null=True),
        ),
        migrations.AddField(
            model_name='aboutus',
            name='description_zh',
            field=models.TextField(default='', null=True),
        ),
        migrations.AddField(
            model_name='aboutus',
            name='title_en',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='aboutus',
            name='title_zh',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='banner',
            name='description_en',
            field=models.TextField(default='', null=True),
        ),
        migrations.AddField(
            model_name='banner',
            name='description_zh',
            field=models.TextField(default='', null=True),
        ),
        migrations.AddField(
            model_name='banner',
            name='title_en',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='banner',
            name='title_zh',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='privacy',
            name='detail_en',
            field=models.TextField(default='', null=True),
        ),
        migrations.AddField(
            model_name='privacy',
            name='detail_zh',
            field=models.TextField(default='', null=True),
        ),
        migrations.AddField(
            model_name='tutorial',
            name='title_en',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='tutorial',
            name='title_zh',
            field=models.CharField(max_length=200, null=True),
        ),
    ]
