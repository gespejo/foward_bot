# coding=utf-8
from __future__ import unicode_literals

from telegram.ext import BaseFilter
from telegram.ext import RegexHandler

from foward_bot.telegram_API import models
from foward_bot.utils.helpers import get_or_none
from foward_bot.utils.filters import CustomFilters
from foward_bot.telegram_API.models import Chat
from .models import AutoForward


def strip_at(username):
    return username[1:len(username)]


def get_chat(update):
    if update.message:
        return update.message.chat
    return update.channel_post.chat


class ForwardMessageFilters(CustomFilters):

    class _TextForwardings(BaseFilter):

        def filter(self, message):
            forwardings = AutoForward.objects.filter(forwarder__id=message.chat.id, enabled=True)
            return len(forwardings) > 0 and message.text and not message.text.startswith('/')

    text_forwardings = _TextForwardings()

    class _OtherForwardings(BaseFilter):

        def filter(self, message):
            forwardings = AutoForward.objects.filter(forwarder__id=message.chat.id, enabled=True)
            return bool(len(forwardings) > 0 and not message.text and (message.audio or message.document or
                                                                       message.photo or message.sticker or
                                                                       message.video or message.contact or
                                                                       message.location or message.venue or
                                                                       message.voice))

    other_forwardings = _OtherForwardings()


class CustomRegexHandler(RegexHandler):

    def check_update(self, update):
        return bool(super(CustomRegexHandler, self).check_update(update) and not
                    update.message.edit_date)


def enable_private():
    chats = Chat.objects.all()
    for chat in chats:
        if chat.type == Chat.PRIVATE and not chat.extra_fields['left']:
            chat.extra_fields['enabled'] = True
            chat.save()
