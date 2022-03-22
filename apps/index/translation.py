from modeltranslation.translator import translator, TranslationOptions
from .models import AboutUs


class AboutUsTranslationOptions(TranslationOptions):
    fields = ('title', 'description')


translator.register(AboutUs, AboutUsTranslationOptions)