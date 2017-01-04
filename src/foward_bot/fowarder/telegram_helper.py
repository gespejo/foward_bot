# coding=utf-8
from __future__ import unicode_literals

import json
import logging

try:
    import django  # noqa
except ImportError as e:
    raise Exception('Need Django installed.')

from telegram import Bot
from telegram import Update
from telegram.ext import Dispatcher

from django.conf.urls import url
from django.http import HttpResponse
from django.views import generic
from django.conf import settings
from django.http.response import Http404
from django.utils.module_loading import import_string
from django.core.urlresolvers import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from foward_bot.telegram_API import models as api_models
from foward_bot.utils.helpers import get_or_none

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class TelegramView(generic.View):

    bots = api_models.Bot.objects.all()
    current_bot = None

    @classmethod
    def as_view(cls, **initkwargs):
        register_webhooks(initkwargs['token'])
        return super(TelegramView, cls).as_view(**initkwargs)

    def get(self, request):
        return HttpResponse()

    def head(self, request):
        return HttpResponse()

    def post(self, request, token):
        dispatcher = get_or_none(api_models.Bot, token=token)
        if not dispatcher:
            return Http404()

        json_string = request.body.decode('utf-8')
        update = Update.de_json(json.loads(json_string), Bot(token))
        self.on_post(update)
        dispatcher.process_update(update)
        return HttpResponse()

    def on_post(self, update):
        pass


class DjangoDispatcher(Dispatcher):

    def __init__(self, bot):
        self.bot = bot

        self.handlers = {}
        """:type: dict[int, list[Handler]"""
        self.groups = []
        """:type: list[int]"""
        self.error_handlers = []

        self.logger = logging.getLogger(__name__)

    def start(self):
        self.logger.warning('DjangoDispatcher do not need start or thread.')


def register_webhooks(token, force=False):

    if not get_or_none(api_models.Bot, token=token):
        BOTS_REGISTERED = {}
        for bot_config in settings.TELEGRAM_BOT:
            if bot_config['token'] is token:
                bot = Bot(bot_config['token'])

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
                bot = Bot(bot_config['token'])
                dispatcher = DjangoDispatcher(bot)
                register = import_string(bot_config['register'])
                register(dispatcher)
                api_models.Bot.objects.create(token=token, dispatcher=bot_config['register'])
                logger.info('bot %s registered on url %s', bot.token, url)


urlpatterns = [
    url(r'^(?P<token>[-_:a-zA-Z0-9]+)/$', TelegramView.as_view(), name='telegram_webhook'),
]
