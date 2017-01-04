# coding=utf-8
from __future__ import unicode_literals

import logging

from telegram import Bot as APIBot, Update
from telegram.ext import Dispatcher
from foward_bot.telegram_API.dispatcher import DjangoDispatcher
from foward_bot.telegram_API import models

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler, RegexHandler
from foward_bot.services.translator import TranslatorServices, Translator
from foward_bot.telegram_API import models
from foward_bot.utils.filters import CustomFilters
from foward_bot.utils.custom_classes import GoodConversationHandler
from foward_bot.utils.helpers import get_or_none
from .models import AutoForward, Languages, Statuses
from .utils import ForwardMessageFilters

# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#                     level=logging.DEBUG)

logger = logging.getLogger(__name__)

fd_username = 'Fowarderbot'


def get_chat(update):
    if update.message:
        return update.message.chat
    return update.channel_post.chat


def get_message(update):
    if update.message:
        return update.message
    return update.channel_post


def send_message(bot, chat_id, **kwargs):
    bot.send_message(chat_id=chat_id, parse_mode='Markdown', **kwargs)


def start(bot, update):
    if update.message.chat.type is models.Chat.CHANNEL:
        resp_admin = update.message.chat.get_administrators()[0]
        for admin in update.message.chat.get_administrators():
            if admin.user.username != bot.username:
                resp_admin = admin
                break
        chat_id = resp_admin.user.id
    else:
        chat_id = update.message.chat_id
    send_message(bot, chat_id, text='Hi, My work is to help you forward messages from one chat'
                                    ' to the other, This is your identifier: %s, use /help '
                                    'to see how you can talk with me' %
                                    models.Chat.objects.get(id=update.message.chat_id))


def help(bot, update):
    bot.send_message(update.message.chat_id, text='This is a help message')


def on_add(bot, update):
    if update.message:
        api_chat = update.message.chat
        chat = get_or_none(models.Chat, id=api_chat.id)
    else:
        api_chat = update.channel_post.chat
        chat = get_or_none(models.Chat, id=api_chat.id)
    if chat.type != models.Chat.PRIVATE:
        for admin in api_chat.get_administrators():
            if not admin.user.username.endswith('bot'):
                if get_or_none(models.User, id=admin.user.id):
                    group_type = api_chat.type
                    send_message(bot, admin.user.id, text='Hello, I was added to the {}: `{}` where you are an admin. '
                                                          'For security purposes I only allow forwarding from groups '
                                                          'if one of the admins approve of it. This is the secret key '
                                                          'of your {}: {}. It will enable users to set forwarding to '
                                                          'and from your {}. Only give this key to those you have '
                                                          'allowed to do so. Have a nice day:)'
                                                          .format(group_type, chat.title,
                                                                  group_type, chat.identifier,
                                                                  group_type))


def echo(bot, update):
    translator = Translator()
    # bot.send_message(update.message.chat_id, text='hello')
    bot.send_message(update.message.chat_id,
                     text=translator.translate(update.message.text, 'ru', service=TranslatorServices.YANDEX))

# AUTO FOWARDING

SENDER, RECEIVER, LANGUAGE = range(3)


def set_auto_forward(bot, update):
    logger.debug('starting the auto forwarding')
    if get_chat(update).type != models.Chat.PRIVATE:
        if get_chat(update).type != models.Chat.CHANNEL:
            update.message.reply_text(
                'Sorry, this command can only be used in a private chat!'
            )
    update.message.reply_text(
            'Hello! It is good you want to set up auto forwarding.'
            'Send /cancel to stop talking to me.\n\n'
            'Please give me the secret key of the chat(group, supergroup or channel) you want to forward from. '
            'You can get it from one of the admins if you don\'t have it. Remember I have to be added to the chat '
            'one of the administrators to be able to forward messages to and from it.',
    )

    return SENDER


def set_sender(bot, update, user_data):
    try:
        sender = get_or_none(models.Chat, identifier=update.message.text)
        if sender is None:
            update.message.reply_text("The key you provided does not exist, "
                                      "please check that it is correct")
            return SENDER
        user_data['sender_id'] = sender.id
        update.message.reply_text("Great, now enter the secret key of the chat(user, group, supergroup or channel) "
                                  "you want me the forward the messages to ")
        return RECEIVER
    except Exception as e:
        logger.error(e.message)
        update.message.reply_text("Oops! Please enter the key correctly")
        return SENDER


lang_choices = list(Languages.choices())
lang_choices.sort()


def set_receiver(bot, update, user_data):
    logger.debug('set_receiver called')
    reply_keyboard = [[label for label, name in lang_choices]]
    try:
        receiver = get_or_none(models.Chat, identifier=update.message.text)
        if receiver is None:
            update.message.reply_text("Unfortunately, the key you provided does not exist, "
                                      "please check that the key is correct. Ask the admins of the chat")
            return RECEIVER
        if receiver.id == user_data['sender_id']:
            update.message.reply_text("Oops! The receiving chat cannot be the same as the as the forwarding chat"
                                      "please enter the correct secret key")
            return RECEIVER
        forwarding = AutoForward.objects.filter(receiver=receiver, forwarder__id=user_data['sender_id'])
        if len(forwarding) > 1:
            update.message.reply_text("Oops! There is already an auto forwarding between these two chats. "
                                      "Note that auto forwarding can only be set in one direction between two chats. "
                                      "Another one cannot be set until the existing one is deleted. Please use /cancel "
                                      "to cancel or enter another chat secret key to continue the setup")
            return RECEIVER
        user_data['receiver_id'] = receiver.id
        update.message.reply_text("We are almost done, now you just have to chose a language to translate the messages"
                                  "to, before forwarding. Choose None if you don't need translating the messages ",
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return LANGUAGE
    except Exception as e:
        logger.error(e.message)
        update.message.reply_text("Oops! Please enter the key correctly")
        return RECEIVER


def set_lang(bot, update, user_data):
    user_data['language'] = update.message.text
    sender = models.Chat.objects.get(id=user_data['sender_id'])
    receiver = models.Chat.objects.get(id=user_data['receiver_id'])
    forwarding, _ = AutoForward.objects.get_or_create(forwarder=sender, receiver=receiver, lang=user_data['language'])
    user_data = {}
    update.message.reply_text("Congratulations! Your auto forwarding has been set and"
                              " should now be up and running!", reply_markup=ReplyKeyboardRemove())

# del delete_auto_forwarding(bot, update, user_data):


def cancel(bot, update, user_data):
    user_data = {}
    update.message.reply_text('Not to worry! We can try setting it again sometime later.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def forward(bot, forwarding, update):
    bot.forward_message(chat_id=forwarding.receiver.id,
                        from_chat_id=forwarding.forwarder.id,
                        message_id=get_message(update).message_id)


def forward_text(bot, update):
    forwardings = AutoForward.objects.filter(forwarder__id=get_chat(update).id)
    for forwarding in forwardings:
        if forwarding.enabled:
            if forwarding.lang == Languages.NONE.value:
                return forward(bot, forwarding, update)
            translator = Translator()
            text = translator.translate(text=get_message(update).text, lang_to=forwarding.lang)
            send_message(bot, forwarding.receiver.id, text=text)


def forward_others(bot, update):
    forwardings = AutoForward.objects.filter(forwarder__id=get_chat(update).id)
    for forwarding in forwardings:
        if forwarding.enabled:
            forward(bot, forwarding, update)


def error(bot, update, error_message):
    logger.error(error_message)
    bot.send_message(get_chat(update).id, text='Sorry, an error occurred:( Try again later')


# this method will be called on start of application
def register(dispatcher):
    # dispatcher.add_handler(CommandHandler('SetAutoForward', set_auto_forward))
    # dispatcher.add_handler(CommandHandler('start', start))
    # dispatcher.add_handler(MessageHandler(Filters.text, echo))
    # # dispatcher.add_handler(CommandHandler('auto_forward', auto_foward, pass_args=True))
    # dispatcher.add_error_handler(error)

    conv_handler = GoodConversationHandler(
                entry_points=[CommandHandler('setAutoForward', set_auto_forward)],

                states={
                    SENDER: [RegexHandler('[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}\Z',
                                          set_sender, pass_user_data=True)],

                    RECEIVER: [RegexHandler('[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}\Z',
                                            set_receiver, pass_user_data=True)],

                    LANGUAGE: [MessageHandler(Filters.text, set_lang, pass_user_data=True)]
                },

                fallbacks=[CommandHandler('cancel', cancel, pass_user_data=True)]
            )
    dispatcher.add_handler(MessageHandler((ForwardMessageFilters.added(fd_username) |
                                           ForwardMessageFilters.channel_added), on_add))
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(MessageHandler(ForwardMessageFilters.text_forwardings, forward_text))
    dispatcher.add_handler(MessageHandler(ForwardMessageFilters.other_forwardings, forward_others))
    dispatcher.add_error_handler(error)

#
# from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
# from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
#                           ConversationHandler)
#
# import logging
#
# # Enable logging
# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#                     level=logging.DEBUG)
#
# logger = logging.getLogger(__name__)
#
# GENDER, PHOTO, LOCATION, BIO = range(4)
#
#
# def start(bot, update):
#     reply_keyboard = [['Boy', 'Girl', 'Other']]
#
#     update.message.reply_text(
#         'Hi! My name is Professor Bot. I will hold a conversation with you. '
#         'Send /cancel to stop talking to me.\n\n'
#         'Are you a boy or a girl?',
#         reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
#
#     return GENDER
#
#
# def gender(bot, update):
#     user = update.message.from_user
#     logger.info("Gender of %s: %s" % (user.first_name, update.message.text))
#     update.message.reply_text('I see! Please send me a photo of yourself, '
#                               'so I know what you look like, or send /skip if you don\'t want to.',
#                               reply_markup=ReplyKeyboardRemove())
#
#     return PHOTO
#
#
# def photo(bot, update):
#     user = update.message.from_user
#     photo_file = bot.getFile(update.message.photo[-1].file_id)
#     photo_file.download('user_photo.jpg')
#     logger.info("Photo of %s: %s" % (user.first_name, 'user_photo.jpg'))
#     update.message.reply_text('Gorgeous! Now, send me your location please, '
#                               'or send /skip if you don\'t want to.')
#
#     return LOCATION
#
#
# def skip_photo(bot, update):
#     user = update.message.from_user
#     logger.info("User %s did not send a photo." % user.first_name)
#     update.message.reply_text('I bet you look great! Now, send me your location please, '
#                               'or send /skip.')
#
#     return LOCATION
#
#
# def location(bot, update):
#     user = update.message.from_user
#     user_location = update.message.location
#     logger.info("Location of %s: %f / %f"
#                 % (user.first_name, user_location.latitude, user_location.longitude))
#     update.message.reply_text('Maybe I can visit you sometime! '
#                               'At last, tell me something about yourself.')
#
#     return BIO
#
#
# def skip_location(bot, update):
#     user = update.message.from_user
#     logger.info("User %s did not send a location." % user.first_name)
#     update.message.reply_text('You seem a bit paranoid! '
#                               'At last, tell me something about yourself.')
#
#     return BIO
#
#
# def bio(bot, update):
#     user = update.message.from_user
#     logger.info("Bio of %s: %s" % (user.first_name, update.message.text))
#     update.message.reply_text('Thank you! I hope we can talk again some day.')
#
#     return ConversationHandler.END
#
#
# def cancel(bot, update):
#     user = update.message.from_user
#     logger.info("User %s canceled the conversation." % user.first_name)
#     update.message.reply_text('Bye! I hope we can talk again some day.',
#                               reply_markup=ReplyKeyboardRemove())
#
#     return ConversationHandler.END
#
#
# def error(bot, update, error):
#     logger.warn('Update "%s" caused error "%s"' % (update, error))
#
#
# def register(dispatcher):
#
#     conv_handler = ConversationHandler(
#         entry_points=[CommandHandler('start', start)],
#
#         states={
#             GENDER: [RegexHandler('^(Boy|Girl|Other)$', gender)],
#
#             PHOTO: [MessageHandler(Filters.photo, photo),
#                     CommandHandler('skip', skip_photo)],
#
#             LOCATION: [MessageHandler(Filters.location, location),
#                        CommandHandler('skip', skip_location)],
#
#             BIO: [MessageHandler(Filters.text, bio)]
#         },
#
#         fallbacks=[CommandHandler('cancel', cancel)]
#     )
#     dispatcher.add_handler(conv_handler)
#     dispatcher.add_error_handler(error)

# Django Telegram Bot settings
token = '297704876:AAHiEy-slaktdaSMJfZtcnoDC-4HQYYDNOs'
mybot = models.Bot.objects.get(token=token)
mybot.set_dispatcher(register)