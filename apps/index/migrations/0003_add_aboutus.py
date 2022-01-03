# Generated by Django 3.2.7 on 2021-12-29 09:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('index', '0002_rename_link'),
    ]

    operations = [
        migrations.CreateModel(
            name='AboutUs',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(null=True)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(null=True)),
                ('image', models.ImageField(null=True, upload_to='')),
                ('model_count', models.IntegerField(default=0)),
                ('format_count', models.IntegerField(default=0)),
                ('render_count', models.IntegerField(default=0)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='index_aboutus_creation', to=settings.AUTH_USER_MODEL)),
                ('updater', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='index_aboutus_update', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]