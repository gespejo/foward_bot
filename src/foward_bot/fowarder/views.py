# coding=utf-8
from __future__ import unicode_literals

import logging

from foward_bot.telegram_API import models as api_models
from foward_bot.telegram_API.views import TelegramView

logger = logging.getLogger(__name__)


class ForwarderView(TelegramView):

    def post(self, request, token):
        extra_fields = {'enabled': False, 'message_counter': 0, 'left': False}
        if 'message' in request.data:
            request.data['message']['chat']['extra_fields'] = extra_fields
        elif 'edited_message' in request.data:
            request.data['edited_message']['chat']['extra_fields'] = extra_fields
        elif 'channel_post' in request.data:
            request.data['channel_post']['chat']['extra_fields'] = extra_fields
        elif 'edited_channel_post' in request.data:
            request.data['edited_channel_post']['chat']['extra_fields'] = extra_fields
        else:
            logger.info('request contains unsupported telegram update type. It will not be handled')
            return
        return super(ForwarderView, self).post(request, token)

