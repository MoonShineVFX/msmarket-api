from django.db import models
from ..user.models import EditorBaseModel, CreatorBaseModel
from ..product.models import Product
from ..storage import PublicGoogleCloudStorage

from google.cloud import storage, exceptions
from django.dispatch import receiver
from django.conf import settings


class Banner(CreatorBaseModel):
    product = models.ForeignKey(Product, on_delete=models.PROTECT)


class Tutorial(EditorBaseModel):
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, default="")
    image = models.ImageField(null=True, upload_to='index/tutorials', storage=PublicGoogleCloudStorage)
    link = models.URLField(null=True)


class AboutUs(EditorBaseModel):
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, default="")
    image = models.ImageField(null=True, upload_to='index/about_us', storage=PublicGoogleCloudStorage)
    model_count = models.IntegerField(default=0)
    format_count = models.IntegerField(default=0)
    render_count = models.IntegerField(default=0)


@receiver(models.signals.post_delete, sender=Tutorial)
def auto_delete_file(sender, instance, **kargs):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(settings.GS_PUBLIC_BUCKET_NAME)
    blob = bucket.blob(instance.file.name)
    try:
        blob.delete()
    except Exception as e:
        print(e)


@receiver(models.signals.pre_save, sender=AboutUs)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes old file from filesystem
    when corresponding `File` object is updated
    with new file.
    """
    if not instance.id:
        return False

    old_file = None
    new_file = None
    try:
        Model = type(instance)
        old_file = Model.objects.get(id=instance.id).image
        new_file = instance.image
    except models.ObjectDoesNotExist:
        return False

    if not old_file:
        return False

    if not old_file == new_file:
        try:
            old_file.storage.delete(name=old_file.name)
        except exceptions.NotFound as e:
            print(e)