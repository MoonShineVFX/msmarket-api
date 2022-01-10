from django.db import models
from ..user.models import EditorBaseModel, CreatorBaseModel
from ..product.models import Product
from ..storage import PublicGoogleCloudStorage


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