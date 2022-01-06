from django.db import models
from apps.user.models import EditorBaseModel
from apps.category.models import Tag
from ..storage import PublicGoogleCloudStorage


def get_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/products/<product_id>/
    if type(instance) == Product:
        return '/'.join(["products", instance.id, filename])
    if type(instance) == Model:
        return '/'.join(["products", instance.product.id, "models", filename])
    if type(instance) == Image:
        return '/'.join(["products", instance.product.id, "images", filename])


class Format(models.Model):
    name = models.CharField(max_length=100)


class Renderer(models.Model):
    name = models.CharField(max_length=100)


class Product(EditorBaseModel):
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=4)
    model_size = models.IntegerField(null=True)
    model_count = models.IntegerField(null=True)
    texture_size = models.CharField(max_length=20, null=True)
    tags = models.ManyToManyField(Tag)
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
    file = models.FileField(upload_to=get_directory_path)
    size = models.IntegerField()


class Image(EditorBaseModel):
    product = models.ForeignKey(Product, related_name="images", on_delete=models.CASCADE)
    file = models.ImageField(upload_to=get_directory_path,
                             storage=PublicGoogleCloudStorage)
    size = models.IntegerField()
    position_id = models.IntegerField(default=1)

    PREVIEW = 1
    MAIN = 2
    MOBILE_MAIN = 3
    THUMB = 4
    EXTEND = 5


class Price(EditorBaseModel):
    product = models.ForeignKey(Product, related_name="prices", on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=4)
    is_current = models.BooleanField(default=False)
