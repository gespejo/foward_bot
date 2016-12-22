# coding=utf-8
from __future__ import unicode_literals

import json

from telegram import Bot as APIBot
from telegram import Update

from django.http import HttpResponse
from django.views import generic
from django.utils.module_loading import import_string
from django.http.response import Http404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from foward_bot.telegram_API.models import Bot
from .models import Bot
from .utils import get_or_none, register_webhooks, DjangoDispatcher


@method_decorator(csrf_exempt, name='dispatch')
class TelegramView(generic.View):

    bot_index = 0

    @classmethod
    def as_view(cls, **initkwargs):
        register_webhooks(bot_index=cls.bot_index)
        return super(TelegramView, cls).as_view(**initkwargs)

    def get(self, request):
        return HttpResponse()

    def head(self, request):
        return HttpResponse()

    def post(self, request, token):
        bot = get_or_none(Bot, token=token)
        if not bot:
            return Http404()

        json_string = request.body.decode('utf-8')
        update = Update.de_json(json.loads(json_string), APIBot(token))
        tg_bot = APIBot(token)
        dispatcher = DjangoDispatcher(tg_bot)
        register = import_string(bot.register)
        register(dispatcher)
        self.on_post(update)
        dispatcher.process_update(update)
        return HttpResponse()

    def on_post(self, update):
        pass