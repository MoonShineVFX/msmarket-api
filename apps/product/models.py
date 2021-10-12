from django.db import models
from apps.account.models import EditorBaseModel
from apps.category.models import Tag
from storages.backends.gcloud import GoogleCloudStorage
from django.conf import settings


def get_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/products/<product_id>/
    return 'products/{0}/{1}'.format(str(instance.product.id), filename)


class Format(models.Model):
    name = models.CharField(max_length=100)


class Renderer(models.Model):
    name = models.CharField(max_length=100)


class Product(EditorBaseModel):
    title = models.CharField(max_length=200)
    preview = models.ImageField(upload_to=get_directory_path,
                                storage=GoogleCloudStorage(bucket=settings.GS_PUBLIC_BUCKET_NAME))
    description = models.TextField()
    model_count = models.IntegerField()
    texture_size = models.IntegerField()
    status = models.IntegerField()


class Model(EditorBaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    format = models.ForeignKey(Format, on_delete=models.CASCADE)
    renderer = models.ForeignKey(Renderer, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag)
    file = models.FileField(upload_to=get_directory_path)
    size = models.IntegerField()


class Image(EditorBaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    file = models.ImageField(upload_to=get_directory_path,
                             storage=GoogleCloudStorage(bucket=settings.GS_PUBLIC_BUCKET_NAME))
    size = models.IntegerField()


class Price(EditorBaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.IntegerField()
    is_current = models.BooleanField(default=False)
