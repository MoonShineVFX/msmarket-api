from django.db import models
from apps.account.models import EditorBaseModel


class Format(models.Model):
    name = models.CharField(max_length=100)


class Renderer(models.Model):
    name = models.CharField(max_length=100)


class Product(EditorBaseModel):
    title = models.CharField(max_length=200)
    description = models.TextField()
    model_count = models.IntegerField()
    texture_size = models.IntegerField()
    status = models.IntegerField()


class Model(EditorBaseModel):
    file = models.FileField()
    size = models.IntegerField()
    format = models.ForeignKey(Format, on_delete=models.CASCADE)
    renderer = models.ForeignKey(Renderer, on_delete=models.CASCADE)


class Image(EditorBaseModel):
    file = models.ImageField()
    size = models.IntegerField()


class Price(EditorBaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.IntegerField()
    is_current = models.BooleanField(default=False)
