# coding=utf-8
from __future__ import unicode_literals

from foward_bot.telegram_API import models as api_models
from foward_bot.telegram_API.views import TelegramView


# class ForwarderView(TelegramView):
#
#     def post(self, request, token):
#         extra_fields = {'initialized': 'False'}
#         if request.data['message']:
#             request.data['message']['chat']['extra_kwargs'] = extra_fields
#         else:
#             request.data['channel_post']['chat']['extra_kwargs'] = extra_fields
#         return super(TelegramView, self).post(request.data, token)

