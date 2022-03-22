from modeltranslation.translator import register, translator, TranslationOptions
from .models import AboutUs, Banner, Tutorial, Privacy


@register(AboutUs)
class AboutUsTranslationOptions(TranslationOptions):
    fields = ('title', 'description')

@register(Banner)
class BannerTranslationOptions(TranslationOptions):
    fields = ('title', 'description')

@register(Tutorial)
class TutorialTranslationOptions(TranslationOptions):
    fields = ('title',)

@register(Privacy)
class PrivacyTranslationOptions(TranslationOptions):
    fields = ('detail',)