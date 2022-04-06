from modeltranslation.translator import register, translator, TranslationOptions
from .models import Tag


@register(Tag)
class AboutUsTranslationOptions(TranslationOptions):
    fields = ('name',)
