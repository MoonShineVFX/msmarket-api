from django.db import models
from apps.user.models import EditorBaseModel
from apps.category.models import Tag
from ..storage import PublicGoogleCloudStorage

from google.cloud import storage
from django.dispatch import receiver
from django.conf import settings


def get_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/products/<product_id>/
    if type(instance) == Model:
        return '/'.join(["static-storage/products", str(instance.product_id), "models", filename])
    if type(instance) == Image:
        return '/'.join(["static-storage/products", str(instance.product_id), "images", filename])


class Format(models.Model):
    name = models.CharField(max_length=100)


class Renderer(models.Model):
    name = models.CharField(max_length=100)


class Product(EditorBaseModel):
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=4)
    model_size = models.BigIntegerField(default=0)
    model_count = models.IntegerField(default=0)
    texture_size = models.CharField(max_length=20, null=True)
    tags = models.ManyToManyField(Tag, blank=True)
    is_active = models.BooleanField(default=False)
    active_at = models.DateTimeField(null=True)
    inactive_at = models.DateTimeField(null=True)

    main_image = models.OneToOneField("Image", null=True, related_name="main_product", on_delete=models.SET_NULL)
    mobile_main_image = models.OneToOneField("Image", null=True, related_name="mobile_main_product", on_delete=models.SET_NULL)
    thumb_image = models.OneToOneField("Image", null=True, related_name="thumb_product", on_delete=models.SET_NULL)
    extend_image = models.OneToOneField("Image", null=True, related_name="extend_product", on_delete=models.SET_NULL)


class Model(EditorBaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="models")
    format = models.ForeignKey(Format, on_delete=models.CASCADE)
    renderer = models.ForeignKey(Renderer, on_delete=models.CASCADE)
    file = models.CharField(max_length=100)
    size = models.BigIntegerField()


class Image(EditorBaseModel):
    product = models.ForeignKey(Product, related_name="images", on_delete=models.CASCADE)
    file = models.ImageField(upload_to=get_directory_path)
    size = models.IntegerField()
    position_id = models.IntegerField(default=1)

    PREVIEW = 1
    MAIN = 2
    MOBILE_MAIN = 3
    THUMB = 4
    EXTEND = 5

    position_2_field = {
        2: "main_image",
        3: "mobile_main_image",
        4: "thumb_image",
        5: "extend_image",
    }

    position_types = [
        {
            "id": 1,
            "key": "preview",
            "name": "商品展示組圖"
        },
        {
            "id": 2,
            "key": "main",
            "name": "詳細頁主圖"
        },
        {
            "id": 3,
            "key": "mobileMain",
            "name": "詳細頁主圖(手機版)"
        },
        {
            "id": 4,
            "key": "thumb",
            "name": "商品列表頁縮圖"
        },
        {
            "id": 5,
            "key": "extend",
            "name": "商品延伸圖(新品、你可能會喜歡)"
        },
    ]


class Price(EditorBaseModel):
    product = models.ForeignKey(Product, related_name="prices", on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=4)
    is_current = models.BooleanField(default=False)


@receiver(models.signals.post_delete, sender=Image)
def auto_delete_file(sender, instance, **kargs):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(settings.GS_BUCKET_NAME)
    blob = bucket.blob(instance.file.name)
    try:
        blob.delete()
    except Exception as e:
        print(e)
