# coding=utf-8
from __future__ import unicode_literals

import logging

from django.core.urlresolvers import reverse
from django.utils.module_loading import import_string
from django.conf import settings
from django.db import connection

from telegram.ext import Dispatcher
from telegram import Bot as TGBot

from .models import Bot


logger = logging.getLogger(__name__)


def get_or_none(model, *args, **kwargs):
    try:
        return model.objects.get(*args, **kwargs)
    except model.DoesNotExist:
        return None


class DjangoDispatcher(Dispatcher):

    def __init__(self, bot):
        super(Dispatcher, self).__init__()
        self.bot = bot

        self.handlers = {}
        """:type: dict[int, list[Handler]"""
        self.groups = []
        """:type: list[int]"""
        self.error_handlers = []

        self.logger = logging.getLogger(__name__)

    def start(self):
        self.logger.warning('DjangoDispatcher do not need start or thread.')


def register_webhooks(bot_index):
    if not db_table_exists("telegram_API_bot"):
        return

    try:
        bot_config = settings.TELEGRAM_BOT[bot_index]
        token = bot_config['token']
        if not get_or_none(Bot, token=token):
            bot = TGBot(token)
            if 'webhook' in bot_config:
                url = bot_config['webhook'] % bot.token
                if url[-1] != '/':
                    url += '/'
            else:
                webhook = reverse('telegram_webhook', kwargs={'token': bot.token})
                from django.contrib.sites.models import Site
                current_site = Site.objects.get_current()
                url = 'https://' + current_site.domain + webhook

            bot.set_webhook(url)
            dispatcher = DjangoDispatcher(bot)
            register = import_string(bot_config['register'])
            register(dispatcher)
            Bot.objects.create(token=token, register=bot_config['register'])
            logger.info('bot %s registered on url %s', bot.token, url)
    except IndexError:
        logger.error("error: index {} does not exist in the TELEGRAM_BOT settings, please check your settings")


def db_table_exists(table_name):
    return table_name in connection.introspection.table_names()

logging.info("Begin")