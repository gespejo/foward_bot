# coding=utf-8
from __future__ import unicode_literals

from foward_bot.telegram_API import models as api_models
from foward_bot.telegram_API.views import TelegramView


class FowarderView(TelegramView):

    def on_post(self, update):
        api_models.Bot.objects.get_or_create()

