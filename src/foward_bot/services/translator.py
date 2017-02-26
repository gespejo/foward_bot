# coding=utf-8
from __future__ import unicode_literals

import goslate
from yandex_translate import YandexTranslate
from yandex_translate import YandexTranslateException
from django.conf import settings

from foward_bot.utils.helpers import SimpleEnum


class TranslatorServices(SimpleEnum):
    GOOGLE = 'google'
    YANDEX = 'yandex'


class Translator(object):

    def __init__(self):
        super(Translator, self).__init__()
        self.yandex_api_key = settings.YANDEX_API_KEY

    def detect_lang(self, text):
        translator = YandexTranslate(self.yandex_api_key)
        return translator.detect(text)

    def translate(self, text, lang_to, lang_from=None,
                  service=TranslatorServices.YANDEX, formatt='plain'):

        if service == TranslatorServices.YANDEX:
            return self.__yandex_translate__(text, lang_to, lang_from, formatt)
        return self.__google_translate__(text, lang_to, lang_from)

    def __yandex_translate__(self, text, lang_to, lang_from, formatt):

        translator = YandexTranslate(self.yandex_api_key)
        try:
            if not lang_from:
                lang_from = self.detect_lang(text)
            lang = "{}-{}".format(lang_from, lang_to)
            translated = translator.translate(text, lang,format=formatt)
            return translated['text'][0]
        except YandexTranslateException:
            return text

    def __google_translate__(self, text, lang_to, lang_from=None):

        gs = goslate.Goslate()
        if not lang_from:
            lang_from = gs.detect(text)
        return gs.translate(text, lang_to, lang_from)
