# coding=utf-8
from __future__ import unicode_literals

import logging
import sys
import traceback


from telegram import Bot as APIBot
from telegram import Update as APIUpdate

from django.http import HttpResponse
from django.utils.module_loading import import_string
from django.utils.decorators import method_decorator
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt

from .models import Bot
from .serializers import BotSerializer, UpdateSerializer, ChannelUpdateSerializer
from .utils import postpone


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@method_decorator(csrf_exempt, name='dispatch')
class TelegramView(APIView):

    bot_index = 0

    def get(self, request, token):
        return HttpResponse()

    def head(self, request):
        return HttpResponse()

    def post(self, request, token):
        self.process_update(request, token)
        return Response(status=status.HTTP_200_OK)

    @postpone
    def process_update(self, request, token):

        if 'message' in request.data or 'edited_message' in request.data:
            serializer = UpdateSerializer(data=request.data)
        elif 'channel_post' in request.data or 'edited_channel_post' in request.data:
            serializer = ChannelUpdateSerializer(data=request.data)
        else:
            logger.info('request contains unsupported telegram update type. It will not be handled')
            return
        if serializer.is_valid():
            serializer.save()
            try:
                bot = Bot.objects.get(token=token)
                bot.handle(APIUpdate.de_json(request.data, APIBot(token)))
                return
            except Bot.DoesNotExist:
                logger.warning("Token %s not associated to a bot" % token)
            except:
                exc_info = sys.exc_info()
                traceback.print_exception(*exc_info)
                logger.error("Error processing %s for token %s" % (request.data, token))
        logger.error("Validation error: %s from message %s" % (serializer.errors, request.data))


class BotViewSet(viewsets.ModelViewSet):
    serializer_class = BotSerializer
    queryset = Bot.objects.all()

    def get_queryset(self):
        return super(BotViewSet, self).get_queryset()