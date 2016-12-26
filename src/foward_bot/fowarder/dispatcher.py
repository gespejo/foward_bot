# coding=utf-8
from __future__ import unicode_literals


from telegram.ext import CommandHandler, MessageHandler, Filters
from foward_bot.services.translator import TranslatorServices, Translator


def start(bot, update):
    bot.send_message(update.message.chat_id, text='Hi from telegram bot inside django project!')


def help(bot, update):
    bot.send_message(update.message.chat_id, text='This is a help message')


def echo(bot, update):
    translator = Translator()
    # bot.send_message(update.message.chat_id, text='hello')
    bot.send_message(update.message.chat_id,
                     text=translator.translate(update.message.text, 'ru', service=TranslatorServices.GOOGLE))


def error(bot, update):
    bot.send_message(update.message.chat_id, text='Command not founded.')


# this method will be called on start of application
def register(dispatcher):
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('help', help))
    dispatcher.add_handler(MessageHandler(Filters.text, echo))
    dispatcher.add_error_handler(error)