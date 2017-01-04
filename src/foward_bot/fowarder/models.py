# coding=utf-8
from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _
from foward_bot.telegram_API.models import Chat
from foward_bot.utils.helpers import SimpleEnum


class Statuses(SimpleEnum):
    ENABLED = True
    DISABLED = False


class Languages(SimpleEnum):
    NONE = 'None'
    ENGLISH = 'en'
    RUSSIAN = 'ru'
    SPANISH = 'es'
    CHINESE = 'zh'
    FRENCH = 'fr'
    ARABIC = 'ar'


class AutoForward(models.Model):
    forwarder = models.ForeignKey(Chat, related_name='forwarder', verbose_name=_("Forwarder"))
    receiver = models.ForeignKey(Chat, related_name='receiver', verbose_name=_("Receiver"))
    enabled = models.BooleanField(_("Status"), default=True)
    lang = models.CharField(_("Language"), max_length=10, choices=Languages.choices(), default=Languages.NONE)

    class Meta:
        unique_together = ('forwarder', 'receiver')



