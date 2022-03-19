# -*- coding: utf-8 -*-
from rest_framework import serializers
from ..user.serializers import EditorBaseSerializer
from .models import LangConfig


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class LangConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = LangConfig
        exclude = ['id', 'lang', 'updated_at']


class LangConfigSearchSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = LangConfig
        exclude = ['id', 'lang', 'updated_at']