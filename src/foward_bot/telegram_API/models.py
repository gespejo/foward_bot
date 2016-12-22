# coding=utf-8
from __future__ import unicode_literals

import uuid

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.forms.models import model_to_dict
from telegram import Bot as APIBot


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

    class Meta:
        verbose_name = _('Bot')
        verbose_name_plural = _('Bots')

    def __init__(self, *args, **kwargs):
        super(Bot, self).__init__(*args, **kwargs)
        self._bot = None
        if self.token:
            self._bot = APIBot(str(self.token))

    def __str__(self):
        return "%s" % (self.user_api.first_name or self.token if self.user_api else self.token)

    def get_me(self):
        return self._bot

    def send_message(self, chat_id, text, parse_mode=None, disable_web_page_preview=None, **kwargs):
        self._bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode,
                              disable_web_page_preview=disable_web_page_preview, **kwargs)

    def foward_message(self, chat_id, from_chat_id, message_id, **kwargs):
        self._bot.forward_message(chat_id=chat_id, from_chat_id=from_chat_id, message_id=message_id, **kwargs)


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