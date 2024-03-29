# coding=utf-8
from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible
from foward_bot.telegram_API.models import Chat, User
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
    GERMAN = 'de'
    HINDI = 'hi'


@python_2_unicode_compatible
class AutoForward(models.Model):
    forwarder = models.ForeignKey(Chat, related_name='forwarder', verbose_name=_("Forwarder"))
    receiver = models.ForeignKey(Chat, related_name='receiver', verbose_name=_("Receiver"))
    enabled = models.BooleanField(_("Enabled"), default=True)
    creator = models.ForeignKey(User, related_name='creator', verbose_name=_('Forwarding Creator'))
    message_header = models.CharField(_('Message Header'), max_length=100, null=True, blank=True)
    message_count = models.BigIntegerField(_('Messages Forwarded'), default=0)
    lang = models.CharField(_("Language"), max_length=10, choices=Languages.choices(), default=Languages.NONE)

    class Meta:
        unique_together = ('forwarder', 'receiver')

    def __str__(self):
        return "From {} to {}".format(self.forwarder, self.receiver)

    def __unicode__(self):
        return "From {} to {}".format(self.forwarder, self.receiver)





