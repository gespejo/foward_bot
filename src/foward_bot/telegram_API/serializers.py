# coding=utf-8
from __future__ import unicode_literals

from datetime import datetime
import time

from rest_framework import serializers

from .models import User, Update, Message, Chat, Bot


class TimestampField(serializers.Field):
    def to_internal_value(self, data):
        return datetime.fromtimestamp(data)

    def to_representation(self, value):
        return int(time.mktime(value.timetuple()))


class UserSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = User
        fields = "__all__"


class BotSerializer(serializers.ModelSerializer):

    class Meta:
        model = Bot
        fields = "__all__"


class ChatSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = Chat
        fields = "__all__"


class MessageSerializer(serializers.ModelSerializer):
    message_id = serializers.IntegerField()
    from_ = UserSerializer(many=False,  source="from_user")
    chat = ChatSerializer(many=False)
    date = TimestampField()

    def __init__(self, *args, **kwargs):
        super(MessageSerializer, self).__init__(*args, **kwargs)
        self.fields['from'] = self.fields['from_']
        del self.fields['from_']

    class Meta:
        model = Message
        fields = ('message_id', 'from_', 'date', 'chat', 'text')


class ChannelMessageSerializer(serializers.ModelSerializer):
    message_id = serializers.IntegerField()
    chat = ChatSerializer(many=False)
    date = TimestampField()

    class Meta:
        model = Message
        fields = ('message_id', 'date', 'chat', 'text')


class UpdateSerializer(serializers.ModelSerializer):

    update_id = serializers.IntegerField()
    message = MessageSerializer()

    class Meta:
        model = Update
        fields = ('update_id', 'message')

    def create(self, validated_data):
        user, _ = User.objects.get_or_create(id=validated_data['message']['from_user']['id'],
                                             defaults=validated_data['message']['from_user'])

        chat, created = Chat.objects.get_or_create(id=validated_data['message']['chat']['id'],
                                                   defaults=validated_data['message']['chat'])
        defaults = validated_data['message'].copy()
        defaults.update({'from_user': user, 'chat': chat})

        message, _ = Message.objects.get_or_create(message_id=validated_data['message']['message_id'],
                                                   defaults=defaults)
        update, _ = Update.objects.get_or_create(update_id=validated_data['update_id'],
                                                 defaults={'update_id': validated_data['update_id'],
                                                 'message': message, 'update_type': Update.MESSAGE})

        return update


class ChannelUpdateSerializer(serializers.ModelSerializer):

    update_id = serializers.IntegerField()
    channel_post = ChannelMessageSerializer()

    class Meta:
        model = Update
        fields = ('update_id', 'channel_post')

    def create(self, validated_data):

        chat, created = Chat.objects.get_or_create(id=validated_data['channel_post']['chat']['id'],
                                                   defaults=validated_data['channel_post']['chat'])
        defaults = validated_data['channel_post'].copy()
        defaults['chat'] = chat

        message, _ = Message.objects.get_or_create(message_id=validated_data['channel_post']['message_id'],
                                                   defaults=defaults)
        update, _ = Update.objects.get_or_create(update_id=validated_data['update_id'],
                                                 defaults={'update_id': validated_data['update_id'],
                                                 'message': message, 'update_type': Update.CHANNEL_POST})

        return update