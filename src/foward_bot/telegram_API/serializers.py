# coding=utf-8
from __future__ import unicode_literals

from datetime import datetime
import time

from rest_framework import serializers

from .models import User, Update, Message, Chat, Bot
from .utils import get_or_none


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
    forward_from = UserSerializer(many=False, required=False)
    chat = ChatSerializer(many=False)
    forward_from_chat = ChatSerializer(many=False, required=False)
    forward_date = TimestampField(required=False)
    date = TimestampField()
    edit_date = TimestampField(required=False)

    def __init__(self, *args, **kwargs):
        super(MessageSerializer, self).__init__(*args, **kwargs)
        self.fields['from'] = self.fields['from_']
        del self.fields['from_']

    class Meta:
        model = Message
        fields = ('message_id', 'from_', 'date', 'chat', 'text', 'edit_date',
                  'entities', 'forward_date', 'forward_from', 'forward_from_chat')
        extra_kwargs = {
            'edit_date': {'required': False},
            'entities': {'required': False},
            'forward_date': {'required': False},
            'forward_from': {'required': False},
            'forward_from_chat': {'required': False},
        }


class ChannelMessageSerializer(serializers.ModelSerializer):
    message_id = serializers.IntegerField()
    chat = ChatSerializer(many=False)
    forward_from = UserSerializer(many=False, required=False)
    forward_from_chat = ChatSerializer(many=False, required=False)
    forward_date = TimestampField(required=False)
    date = TimestampField()
    edit_date = TimestampField(required=False)

    class Meta:
        model = Message
        fields = ('message_id', 'date', 'chat', 'text', 'edit_date',
                  'entities', 'forward_date', 'forward_from', 'forward_from_chat')
        extra_kwargs = {
            'edit_date': {'required': False},
            'entities': {'required': False},
            'forward_date': {'required': False},
            'forward_from': {'required': False},
            'forward_from_chat': {'required': False},
        }


class UpdateSerializer(serializers.ModelSerializer):

    update_id = serializers.IntegerField()
    message = MessageSerializer()

    def __init__(self, *args, **kwargs):
        if 'edited_message' in kwargs['data']:
            kwargs['data']['message'] = kwargs['data']['edited_message']
            del kwargs['data']['edited_message']
        super(UpdateSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = Update
        fields = ('update_id', 'message',)
        # extra_kwargs = {
        #     'message': {'required': False},
        #     'edited_message': {'required': False},
        # }

    def create(self, validated_data):
        root = 'message'
        if 'edited_message' in validated_data:
            root = 'edited_message'
        chat, created = Chat.objects.get_or_create(id=validated_data[root]['chat']['id'],
                                                   defaults=validated_data[root]['chat'])
        if chat.type == Chat.PRIVATE:

            user, _ = User.objects.get_or_create(id=validated_data[root]['from_user']['id'],
                                                 defaults=validated_data[root]['from_user'])
        else:
            user = get_or_none(User, id=validated_data[root]['from_user']['id'])

        defaults = validated_data[root].copy()
        defaults['chat'] = chat
        if user:
            defaults['from_user'] = user
        else:
            del defaults['from_user']
        if 'forward_from' in defaults:
            forward_from = get_or_none(User, id=defaults['forward_from']['id'])
            if forward_from:
                defaults['forward_from'] = forward_from
            else:
                del defaults['forward_from']

        if 'forward_from_chat' in defaults:
            forward_from_chat = get_or_none(Chat, id=defaults['forward_from_chat']['id'])
            if forward_from_chat:
                defaults['forward_from_chat'] = forward_from_chat
            else:
                del defaults['forward_from_chat']

        message, _ = Message.objects.get_or_create(message_id=validated_data[root]['message_id'],
                                                   defaults=defaults)
        update, _ = Update.objects.get_or_create(update_id=validated_data['update_id'],
                                                 defaults={'update_id': validated_data['update_id'],
                                                 'message': message, 'update_type': root})

        return update


class ChannelUpdateSerializer(serializers.ModelSerializer):

    update_id = serializers.IntegerField()
    channel_post = ChannelMessageSerializer(many=False)

    def __init__(self, *args, **kwargs):
        if 'edited_channel_post' in kwargs['data']:
            kwargs['data']['channel_post'] = kwargs['data']['edited_channel_post']
            del kwargs['data']['edited_channel_post']
        super(ChannelUpdateSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = Update
        fields = ('update_id', 'channel_post')
        # extra_kwargs = {
        #     'channel_post': {'required': False},
        #     'edited_channel_post': {'required': False},
        # }

    def create(self, validated_data):
        root = 'channel_post'
        if 'edited_channel_post' in validated_data:
            root = 'edited_channel_post'

        chat, _ = Chat.objects.get_or_create(id=validated_data[root]['chat']['id'],
                                             defaults=validated_data[root]['chat'])

        defaults = validated_data[root].copy()
        defaults['chat'] = chat

        if 'forward_from' in defaults:
            forward_from = get_or_none(User, id=defaults['forward_from']['id'])
            if forward_from:
                defaults['forward_from'] = forward_from
            else:
                del defaults['forward_from']

        if 'forward_from_chat' in defaults:
            forward_from_chat = get_or_none(Chat, id=defaults['forward_from_chat']['id'])
            if forward_from_chat:
                defaults['forward_from_chat'] = forward_from_chat
            else:
                del defaults['forward_from_chat']

        message, _ = Message.objects.get_or_create(message_id=validated_data[root]['message_id'],
                                                   defaults=defaults)
        update, _ = Update.objects.get_or_create(update_id=validated_data['update_id'],
                                                 defaults={'update_id': validated_data['update_id'],
                                                 'message': message, 'update_type': root})

        return update