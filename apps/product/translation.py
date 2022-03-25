from modeltranslation.translator import register, translator, TranslationOptions
from .models import Product


@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = ('title', 'description')