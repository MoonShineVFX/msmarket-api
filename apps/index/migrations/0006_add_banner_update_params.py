# Generated by Django 3.2.7 on 2022-01-19 07:59

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('index', '0005_change_banner_columns'),
    ]

    operations = [
        migrations.AddField(
            model_name='banner',
            name='updated_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='banner',
            name='updater',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='index_banner_update', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='banner',
            name='creator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='index_banner_creation', to=settings.AUTH_USER_MODEL),
        ),
    ]