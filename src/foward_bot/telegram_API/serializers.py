# coding=utf-8
from __future__ import unicode_literals

from rest_framework import serializers

from .models import User, Update, Message, Chat, Bot


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = "__all__"


class BotSerializer(serializers.ModelSerializer):

    class Meta:
        model = Bot
        fields = "__all__"


class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = "__all__"


class MessageSerializer(serializers.ModelSerializer):

    from_user = UserSerializer(many=False)
    chat = ChatSerializer(many=False)

    class Meta:
        model = Message
        fields = "__all__"


class UpdateSerializer(serializers.ModelSerializer):

    message = MessageSerializer()

    class Meta:
        model = Update
        fields = "__all__"
