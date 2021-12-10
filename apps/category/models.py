from django.db import models
from ..user.models import EditorBaseModel


category = {
    "all": "全部",
    "new": "新品",
    "sale": "特價",
    "free": "免費"
}

category_key_2_id = {
    "new": 1,
    "sale": 2,
    "free": 3
}


class Tag(EditorBaseModel):
    name = models.CharField(max_length=100)
