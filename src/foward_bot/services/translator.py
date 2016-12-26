# coding=utf-8
from __future__ import unicode_literals

import goslate
from yandex_translate import YandexTranslate
from django.conf import settings

from foward_bot.utils.helpers import SimpleEnum


class TranslatorServices(SimpleEnum):
    GOOGLE = 'google'
    YANDEX = 'yandex'


class Translator(object):

    def __init__(self):
        super(Translator, self).__init__()
        self.yandex_api_key = settings.YANDEX_API_KEY

    def translate(self, text, lang_to, lang_from=None,
                  service=TranslatorServices.YANDEX):

        if service == TranslatorServices.YANDEX:
            return self.__yandex_translate__(text, lang_to, lang_from)
        return self.__google_translate__(text, lang_to, lang_from)

    def __yandex_translate__(self, text, lang_to, lang_from=None):

        translator = YandexTranslate(self.yandex_api_key)
        if not lang_from:
            lang_from = translator.detect(text)
        lang = "{}-{}".format(lang_from, lang_to)
        translated = translator.translate(text, lang)
        return translated['text'][0]

    def __google_translate__(self, text, lang_to, lang_from=None):

        gs = goslate.Goslate()
        if not lang_from:
            lang_from = gs.detect(text)
        return gs.translate(text, lang_to, lang_from)


