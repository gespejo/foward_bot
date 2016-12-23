# coding=utf-8
from __future__ import unicode_literals

import uuid
import logging

from django.db import models
from django.core.urlresolvers import reverse
from django.utils.module_loading import import_string
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.forms.models import model_to_dict
from django.contrib.sites.models import Site
from django.dispatch import receiver
from django.db.models.signals import post_save
from telegram import Bot as APIBot

from .dispatcher import DjangoDispatcher

logger = logging.getLogger(__file__)


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(_("Date created"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date updated"), auto_now=True)

    class Meta:
        abstract = True


class Bot(models.Model):
    token = models.CharField(_('Token'), max_length=100, db_index=True)
    register = models.CharField(_('Register'), max_length=1000, blank=True)
    # user_api = models.OneToOneField(User, verbose_name=_("Bot User"), related_name='bot',
    #                                 on_delete=models.CASCADE, blank=True, null=True)
    ssl_certificate = models.FileField(_("SSL certificate"), upload_to='telegrambot/ssl/',
                                       blank=True, null=True)
    enabled = models.BooleanField(_('Enable'), default=True)
    created = models.DateTimeField(_('Date Created'), auto_now_add=True)
    modified = models.DateTimeField(_('Date Modified'), auto_now=True)
    site = models.OneToOneField(Site, verbose_name=_('Site'), blank=True, null=True)

    class Meta:
        verbose_name = _('Bot')
        verbose_name_plural = _('Bots')

    def __init__(self, *args, **kwargs):
        super(Bot, self).__init__(*args, **kwargs)
        self._bot = None
        if self.token:
            self._bot = APIBot(str(self.token))

    def __str__(self):
        return "%s" % self.token

    def get_me(self):
        return self._bot

    def handle(self, update):

        dispatcher = DjangoDispatcher(self._bot)
        register = import_string(self.register)
        register(dispatcher)
        dispatcher.process_update(update)

    def send_message(self, chat_id, text, parse_mode=None, disable_web_page_preview=None, **kwargs):
        self._bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode,
                              disable_web_page_preview=disable_web_page_preview, **kwargs)

    def foward_message(self, chat_id, from_chat_id, message_id, **kwargs):
        self._bot.forward_message(chat_id=chat_id, from_chat_id=from_chat_id, message_id=message_id, **kwargs)


@receiver(post_save, sender=Bot)
def set_api(sender, instance, **kwargs):
    #  set bot api if not yet
    if not instance._bot:
        instance._bot = APIBot(instance.token)

    # set webhook
    url = None
    cert = None
    if instance.enabled:
        webhook = reverse('api_webhook', args={instance.token})
        # webhook = '/webhook/' + instance.token + '/'
        url = 'https://' + instance.site.domain + webhook
    if instance.ssl_certificate:
        cert = instance.ssl_certificate.open()
    instance._bot.setWebhook(webhook_url=url,
                             certificate=cert)
    logger.info("Success: Webhook url %s for bot %s set" % (url, str(instance)))

    #  complete  Bot instance with api data
    # if not instance.user_api:
    #     bot_api = instance._bot.getMe()
    #     user_api, _ = User.objects.get_or_create(**bot_api.to_dict())
    #     instance.user_api = user_api
    #     instance.save()
    #     logger.info("Success: Bot api info for bot %s set" % str(instance))


@python_2_unicode_compatible
class User(models.Model):
    id = models.BigIntegerField(primary_key=True)
    first_name = models.CharField(_('First name'), max_length=255)
    last_name = models.CharField(_('Last name'), max_length=255, blank=True, null=True)
    username = models.CharField(_('User name'), max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def __str__(self):
        return "%s" % self.first_name

    def to_dict(self):
        return model_to_dict(self)


@python_2_unicode_compatible
class Chat(models.Model):
    PRIVATE, GROUP, SUPERGROUP, CHANNEL = 'private', 'group', 'supergroup', 'channel'

    TYPE_CHOICES = (
        (PRIVATE, _('Private')),
        (GROUP, _('Group')),
        (SUPERGROUP, _('Supergroup')),
        (CHANNEL, _('Channel')),
    )

    id = models.BigIntegerField(primary_key=True)
    type = models.CharField(max_length=255, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255, null=True, blank=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = _('Chat')
        verbose_name_plural = _('Chats')

    def __str__(self):
        return "%s" % self.id

    def to_dict(self):
        return model_to_dict(self)


@python_2_unicode_compatible
class Message(BaseModel):
    message_id = models.BigIntegerField(_('Id'), db_index=True)  # It is no unique. Only combined with chat and bot
    from_user = models.ForeignKey(User, related_name='messages', verbose_name=_("User"))
    date = models.DateTimeField(_('Date'))
    chat = models.ForeignKey(Chat, related_name='messages', verbose_name=_("Chat"))
    forward_from = models.ForeignKey(User, null=True, blank=True, related_name='forwarded_from',
                                     verbose_name=_("Forward from"))
    text = models.TextField(null=True, blank=True, verbose_name=_("Text"))

    #  TODO: complete fields with all message fields

    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['-date', ]

    def __str__(self):
        return "(%s,%s,%s)" % (self.message_id, self.chat, self.text or '(no text)')

    def to_dict(self):
        message_dict = model_to_dict(self, exclude=['from_user', 'chat'])
        message_dict.update({'from_user': self.from_user.to_dict(),
                             'chat': self.chat.to_dict()})

        return message_dict


class Update(BaseModel):
    bot = models.ForeignKey('Bot', verbose_name=_("Bot"), related_name="updates")
    update_id = models.BigIntegerField(_('Update Id'), db_index=True)
    message = models.ForeignKey(Message, null=True, blank=True, verbose_name=_('Message'),
                                related_name="updates")

    class Meta:
        verbose_name = 'Update'
        verbose_name_plural = 'Updates'
        unique_together = ('update_id', 'bot')

    def __str__(self):
        return "(%s, %s)" % (self.bot.id, self.update_id)

    def to_dict(self):
        if self.message:
            return {'update_id': self.update_id, 'message': self.message.to_dict()}
        elif self.callback_query:
            return {'update_id': self.update_id, 'callback_query': self.callback_query.to_dict()}