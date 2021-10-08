from django.db import models
from ..account.models import EditorBaseModel


class Tag(EditorBaseModel):
    name = models.CharField(max_length=100)
