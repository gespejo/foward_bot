# coding=utf-8
from __future__ import unicode_literals

import logging
from telegram.ext import BaseFilter

from foward_bot.telegram_API import models
from .helpers import get_or_none

logger = logging.getLogger(__name__)


class CustomFilters:
    """
    Custom defined filters for use with the `filter` argument of :class:`telegram.ext.MessageHandler`.
    """

    class _Added(BaseFilter):

        def __init__(self, username):
            self.username = username

        def filter(self, message, username=None):
            answer = bool(message.new_chat_member and message.new_chat_member.username == self.username)
            return answer

    added = _Added

    class _ChannelAdded(BaseFilter):

        def filter(self, message):
            if message.chat.type == models.Chat.CHANNEL:
                try:
                    messages = models.Message.objects.filter(chat__id=message.chat.id)
                    return len(messages) == 1
                except Exception:
                    logger.exception('An error occurred while using the channel_added filter')

            return False

    channel_added = _ChannelAdded()

    class _NonChannelMessages(BaseFilter):

        def filter(self, message):
            return message.chat.type == models.Chat.CHANNEL
