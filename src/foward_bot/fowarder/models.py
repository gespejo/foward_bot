# coding=utf-8
from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _
from foward_bot.telegram_API.models import Chat
from foward_bot.utils.helpers import SimpleEnum


class Statuses(SimpleEnum):
    ENABLED = 'google'
    DISABLED = 'yandex'


class Languages(SimpleEnum):
    ENGLISH = 'en'
    RUSSIAN = 'ru'
    SPANISH = 'es'
    CHINESE = 'zh'
    FRENCH = 'fr'
    ARABIC = 'ar'


class AutoForward(models.Model):
    forwarder = models.ForeignKey(Chat, related_name='forwarder', verbose_name=_("Forwarder"))
    receiver = models.ForeignKey(Chat, related_name='receiver', verbose_name=_("Receiver"))
    status = models.BooleanField(_("Status"), choices=Statuses.choices(), default=Statuses.ENABLED)
    lang = models.CharField(_("Language"), max_length=2, choices=Languages.choices(), null=True)
