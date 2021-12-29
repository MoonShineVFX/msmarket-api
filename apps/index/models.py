from django.db import models
from ..user.models import EditorBaseModel, CreatorBaseModel
from ..product.models import Product


class Banner(CreatorBaseModel):
    product = models.ForeignKey(Product, on_delete=models.PROTECT)


class Tutorial(EditorBaseModel):
    title = models.CharField(max_length=200)
    description = models.TextField(null=True)
    image = models.ImageField(null=True)
    link = models.URLField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
