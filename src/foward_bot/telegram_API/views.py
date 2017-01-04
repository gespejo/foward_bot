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
from .utils import register_webhooks


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
        serializer = UpdateSerializer(data=request.data)
        if not serializer.is_valid():
            serializer = ChannelUpdateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            try:
                bot = Bot.objects.get(token=token)
                bot.handle(APIUpdate.de_json(request.data, APIBot(token)))
                return Response(status=status.HTTP_200_OK)
            except Bot.DoesNotExist:
                logger.warning("Token %s not associated to a bot" % token)
                return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)
            except:
                exc_info = sys.exc_info()
                traceback.print_exception(*exc_info)
                logger.error("Error processing %s for token %s" % (request.data, token))
                return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        logger.error("Validation error: %s from message %s" % (serializer.errors, request.data))
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BotViewSet(viewsets.ModelViewSet):
    serializer_class = BotSerializer
    queryset = Bot.objects.all()

    def get_queryset(self):
        return super(BotViewSet, self).get_queryset()