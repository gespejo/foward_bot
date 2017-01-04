# coding=utf-8
from __future__ import unicode_literals

from telegram.ext import BaseFilter

from foward_bot.telegram_API import models
from foward_bot.utils.helpers import get_or_none
from foward_bot.utils.filters import CustomFilters
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
            forwardings = AutoForward.objects.filter(forwarder__id=message.chat.id)
            return len(forwardings) > 0 and message.text

    text_forwardings = _TextForwardings()

    class _OtherForwardings(BaseFilter):

        def filter(self, message):
            forwardings = AutoForward.objects.filter(forwarder__id=message.chat.id)
            return len(forwardings) > 0 and not message.text

    other_forwardings = _OtherForwardings()



