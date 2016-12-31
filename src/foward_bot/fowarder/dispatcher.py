# coding=utf-8
from __future__ import unicode_literals

from foward_bot.telegram_API.models import Chat
from foward_bot.utils.helpers import get_or_none

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler, RegexHandler
from foward_bot.services.translator import TranslatorServices, Translator
from foward_bot.telegram_API.models import Chat, Bot
from .models import AutoForward, Languages
from .utils import strip_at


def start(bot, update):
    if update.message.chat.type is Chat.CHANNEL:
        resp_admin = update.message.chat.getAdministators()[0]
        for admin in update.message.chat.getAdministators():
            if admin.username != bot.username:
                resp_admin = admin
                break
        chat_id = resp_admin.id
    else:
        chat_id = update.message.chat_id
    bot.send_message(chat_id, text='Hi, My work is to help you forward messages from one chat'
                                   ' to the other, This is your identifier: %s, use /help '
                                   'to see how you can talk with me' %
                                   Chat.objects.get(id=update.message.chat_id))


def help(bot, update):
    bot.send_message(update.message.chat_id, text='This is a help message')


def echo(bot, update):
    translator = Translator()
    # bot.send_message(update.message.chat_id, text='hello')
    bot.send_message(update.message.chat_id,
                     text=translator.translate(update.message.text, 'ru', service=TranslatorServices.YANDEX))

    # AUTO FOWARDING

SENDER, RECEIVER, LANGUAGE = range(3)


def set_auto_forward(bot, update):
    update.message.reply_text(
            'Hello! It is good you want to set up auto forwarding.'
            'Send /cancel to stop talking to me.\n\n'
            'Please give me the identifier of the chat(group, supergroup or channel) you want to forward from',
    )

    return SENDER


def set_sender(bot, update, user_data):
    try:
        sender_username = strip_at(update.message.text)
        sender = get_or_none(Chat, id=sender_username)
        if sender is None:
            update.message.reply_text("The username you provided is not correct or "
                                      "is not does not use my services, please check that it is correct and uses me")
            return SENDER
        user_data['sender_id'] = sender.id
        update.message.reply_text("Great, now enter the username of the chat(user, group, supergroup or channel) "
                                  "you want me the forward the messages to ")
        return RECEIVER
    except:
        update.message.reply_text("Oops! Please enter the username correctly")
        return SENDER


lang_choices = ['None']
lang_choices += list(Languages.choices())


def set_receiver(bot, update, user_data):
    reply_keyboard = [lang_choices]
    try:
        receiver_username = strip_at(update.message.text)
        receiver = get_or_none(Chat, id=receiver_username)
        if receiver is None:
            update.message.reply_text("Unfortunately, the username you provided does not belong to any chat that I take part in "
                                      "please check I belong to the group, channel or chat with the username")
            return RECEIVER
        if receiver is user_data['sender']:
            update.message.reply_text("Oops! The receiving chat cannot be the same as the as the forwarding chat"
                                      "please choose another username")
            return RECEIVER
        user_data['receiver_id'] = receiver.id
        update.message.reply_text("We are almost done, now you just have to chose a language to translate the messages"
                                  "to, before forwarding. Choose None if you don't need translating the messages ",
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return LANGUAGE
    except:
        update.message.reply_text("Oops! Please enter the username correctly")
        return RECEIVER


def set_lang(bot, update, user_data):
    user_data['language'] = update.message.text
    sender = Chat.objects.get(id=user_data['sender_id'])
    receiver = Chat.objects.get(id=user_data['receiver_id'])
    if user_data['language'] is 'None':
        AutoForward.objects.create(forwarder=sender, receiver=receiver)
    else:
        AutoForward.objects.create(forwarder=sender, receiver=receiver, lang=user_data['language'])
    user_data = {}
    update.message.reply_text("Congratulations! Your auto forwarding has been set and"
                              " should now be up and running!", reply_markup=ReplyKeyboardRemove)


def cancel(bot, update, user_data):
    user_data = {}
    update.message.reply_text('Not to worry! We can try setting it again sometime later.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error(bot, update):
    bot.send_message(update.message.chat_id, text='Command not founded.')


# this method will be called on start of application
def register(dispatcher):
    # dispatcher.add_handler(CommandHandler('SetAutoForward', set_auto_forward))
    # dispatcher.add_handler(CommandHandler('start', start))
    # dispatcher.add_handler(MessageHandler(Filters.text, echo))
    # # dispatcher.add_handler(CommandHandler('auto_forward', auto_foward, pass_args=True))
    # dispatcher.add_error_handler(error)

    conv_handler = ConversationHandler(
            entry_points=[CommandHandler('setAutoForward', set_auto_forward)],

            states={
                SENDER: [RegexHandler('^d+', set_sender, pass_user_data=True)],

                RECEIVER: [RegexHandler('^d+', set_receiver, pass_user_data=True)],

                LANGUAGE: [MessageHandler(Filters.text, set_lang, pass_user_data=True)]
            },

            fallbacks=[CommandHandler('cancel', cancel, pass_user_data=True)]
        )
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(conv_handler)
    dispatcher.add_error_handler(error)


# from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
# from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
#                           ConversationHandler)
#
# import logging
#
# # Enable logging
# logger = logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#                              level=logging.DEBUG)
#
# # logger = logging.getLogger(__name__)
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