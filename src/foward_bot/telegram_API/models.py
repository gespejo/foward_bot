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
from django.contrib.postgres.fields import JSONField
from django.contrib.sites.models import Site
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save
from telegram.ext import Dispatcher
from telegram import Bot as APIBot


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

    def set_dispatcher(self, register):
        api_bot = APIBot(self.token)
        dispatcher = Dispatcher(api_bot, None)
        register(dispatcher)
        dispatchers[self.token] = dispatcher

    def get_me(self):
        return self._bot

    def set_webhook(self):
        set_api(Chat, self)

    def handle(self, update):
        dispatchers[self.token].process_update(update)

    def send_message(self, chat_id, text, parse_mode=None, disable_web_page_preview=None, **kwargs):
        self._bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode,
                               disable_web_page_preview=disable_web_page_preview, **kwargs)

    def forward_message(self, chat_id, from_chat_id, message_id, **kwargs):
        self._bot.forward_message(chat_id=chat_id, from_chat_id=from_chat_id, message_id=message_id, **kwargs)


@receiver(post_save, sender=Bot)
def set_api(sender, instance, **kwargs):
    print("set_api method was called")
    #  set bot api if not yet
    if not instance._bot:
        instance._bot = APIBot(instance.token)

    # set webhook
    web_url = None
    cert = None
    if instance.enabled:
        if instance.token in webhook_urls:
            webhook = webhook_urls[instance.token]
        else:
            namespace = 'telegram_API:webhook'
            webhook = reverse(namespace, kwargs={'token': instance.token})
        web_url = 'https://' + instance.site.domain + webhook
        if instance.ssl_certificate:
            cert = instance.ssl_certificate.open()
    instance._bot.setWebhook(webhook_url=web_url,
                             certificate=cert)
    logger.info("Success: Web hook url %s for bot %s set" % (web_url, str(instance)))


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

    CHAT_TYPE_CHOICES = (
        (PRIVATE, _('Private')),
        (GROUP, _('Group')),
        (SUPERGROUP, _('Supergroup')),
        (CHANNEL, _('Channel')),
    )

    id = models.BigIntegerField(_('Id'), primary_key=True)
    identifier = models.UUIDField(_('Identifier'), default=uuid.uuid4, editable=False, unique=True)
    type = models.CharField(_('Type'), max_length=255, choices=CHAT_TYPE_CHOICES)
    title = models.CharField(_('Title'), max_length=255, null=True, blank=True)
    username = models.CharField(_('Username'), max_length=255, null=True, blank=True)
    first_name = models.CharField(_('First Name'), max_length=255, null=True, blank=True)
    last_name = models.CharField(_('Last Name'), max_length=255, null=True, blank=True)

    extra_fields = JSONField(verbose_name='Extra Fields', null=True, blank=True)

    class Meta:
        verbose_name = _('Chat')
        verbose_name_plural = _('Chats')

    def __str__(self):
        return "%s" % self.id

    def to_dict(self):
        return model_to_dict(self)


@python_2_unicode_compatible
class Message(models.Model):
    message_id = models.BigIntegerField(_('Message Id'))  # It is no unique. Only combined with chat and bot
    from_user = models.ForeignKey(User, related_name='messages', verbose_name=_("User"), null=True)
    date = models.DateTimeField(_('Date'))
    chat = models.ForeignKey(Chat, related_name='messages', verbose_name=_("Chat"), null=True)
    text = models.TextField(null=True, blank=True, verbose_name=_("Text"))
    edit_date = models.DateTimeField(_('Edit Date'), null=True, blank=True)
    entities = JSONField(verbose_name=_('Entities'), null=True, blank=True)
    forward_date = models.DateTimeField(_('Forward Date'), null=True, blank=True)
    forward_from = models.ForeignKey(User, null=True, blank=True, related_name='forwarded_from',
                                     verbose_name=_("Forward from"))
    forward_from_chat = models.ForeignKey(Chat, related_name='forwarded_messages',
                                          verbose_name=_('Forward From Chat'), null=True, blank=True)

    #  TODO: complete fields with all message fields especially for forwarding fields

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


class Update(models.Model):
    MESSAGE, CHANNEL_POST, EDITED_MESSAGE, EDITED_CHANNEL_POST = 'message', 'channel_post', 'edited_message', \
                                                                 'edited_channel_post',

    UPDATE_CHOICES = (
        (MESSAGE, _('Message')),
        (CHANNEL_POST, _('Channel Post')),
        (MESSAGE, _('Edited Message')),
        (CHANNEL_POST, _('Edited Channel Post')),
    )
    update_id = models.BigIntegerField(_('Id'), primary_key=True)
    message = models.ForeignKey(Message, null=True, blank=True, verbose_name=_('Message'),
                                related_name="updates")
    update_type = models.CharField(_('Update Type'), max_length=20, choices=UPDATE_CHOICES, default=MESSAGE)

    class Meta:
        verbose_name = 'Update'
        verbose_name_plural = 'Updates'

    def __str__(self):
        return "%s" % self.update_id


def set_webhook_url(token, app_name, **kwargs):
    webhook_urls[token] = app_name


dispatchers = {}
webhook_urls = {}