# coding=utf-8
from __future__ import unicode_literals

import json
import logging

from telegram import Bot as APIBot
from telegram import Update

from django.http import HttpResponse
from django.utils.module_loading import import_string
from django.utils.decorators import method_decorator
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt

from .models import Bot
from .serializers import UpdateSerializer
from .utils import register_webhooks


logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class TelegramView(APIView):

    bot_index = 0

    # @classmethod
    # def as_view(cls, **initkwargs):
    #     register_webhooks(bot_index=cls.bot_index)
    #     return super(TelegramView, cls).as_view(**initkwargs)

    def get(self, request):
        return HttpResponse()

    def head(self, request):
        return HttpResponse()

    def post(self, request, token):
        serializer = UpdateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            try:
                bot = Bot.objects.get(token=token)
                bot.handle(Update.de_json(request.data, APIBot(token)))
            except Bot.DoesNotExist:
                logger.warning("Token %s not associated to a bot" % token)
        return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)


logging.info("Begin")