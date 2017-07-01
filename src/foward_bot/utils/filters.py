# coding=utf-8
from __future__ import unicode_literals

import logging
from telegram.ext import BaseFilter

from foward_bot.telegram_API import models
from .helpers import get_or_none

logger = logging.getLogger(__name__)


class CustomFilters(object):
    """
    Custom defined filters for use with the `filter` argument of :class:`telegram.ext.MessageHandler`.
    """

    class _Added(BaseFilter):

        def __init__(self, username):
            self.username = username

        def filter(self, message, username=None):
            return bool(message.new_chat_member and message.new_chat_member.username == self.username)

    added = _Added

    class _ChannelAdded(BaseFilter):

        def filter(self, message):
            if message.chat.type == models.Chat.CHANNEL:
                chat = get_or_none(models.Chat, id=message.chat.id)
                if chat is None:
                    logger.error('An error occurred while using the channel_added filter')
                else:
                    return not chat.extra_fields['enabled']
            return False

    channel_added = _ChannelAdded()

    class _Removed(BaseFilter):

        def __init__(self, username):
            self.username = username

        def filter(self, message, username=None):
            return bool(message.left_chat_member and message.left_chat_member.username == self.username)

    removed = _Removed

    class _ChannelRemoved(BaseFilter):

        def filter(self, message):
            if message.chat.type == models.Chat.CHANNEL:
                chat = get_or_none(models.Chat, id=message.chat.id)
                if chat is None:
                    logger.error('An error occurred while using the channel_added filter')
                else:
                    return not chat.extra_fields['initialized']
            return False

    channel_removed = _ChannelRemoved()

    class _NonChannelMessages(BaseFilter):

        def filter(self, message):
            return message.chat.type == models.Chat.CHANNEL

