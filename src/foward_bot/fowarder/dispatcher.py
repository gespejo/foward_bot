# coding=utf-8
from __future__ import unicode_literals

import logging

from telegram import error as api_error
from telegram import Chat as APIChat

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler
from django.conf import settings
from foward_bot.services.translator import TranslatorServices, Translator
from foward_bot.telegram_API import models
from foward_bot.utils.custom_classes import GoodConversationHandler
from foward_bot.utils.helpers import get_or_none
from .models import AutoForward, Languages
from .utils import ForwardMessageFilters, CustomRegexHandler

# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#                     level=logging.DEBUG)

logger = logging.getLogger(__name__)

fd_username = settings.SECRETS['bot']['username']
HTML = 'HTML'
markdown = 'Markdown'
enabled = 'enabled'
dev_username = settings.SECRETS['developer']['username']

timeouts = settings.MESSAGE_TIMEOUTS

# TODO: Fix production mode logger to log errors to files and info to console


def escape_markdown(text):
    text = text.replace('_', '\_')
    text = text.replace('*', '\*')
    text = text.replace('`', '\`')
    return text.replace('```', '```')


def get_message(update):
    if update.message:
        return update.message
    elif update.edited_message:
        return update.edited_message
    elif update.channel_post:
        return update.channel_post
    return update.edited_channel_post


def get_chat(update):
    return get_message(update).chat


def del_update_and_message(update):
    myupdate = get_or_none(models.Update, update_id=update.update_id)
    if myupdate:
        myupdate.delete()
    message = get_or_none(models.Message, message_id=get_message(update).message_id)
    if message:
        message.delete()


def send_message(bot, chat_id, text, **kwargs):
    try:
        bot.send_message(chat_id=chat_id, parse_mode=markdown, text=text, **kwargs)
    except api_error.TelegramError as tg_error:
        logger.info('Probably a wrong markup. Will escape characters and retry send_message. Error: {}'.
                    format(tg_error.message))
        bot.send_message(chat_id=chat_id, parse_mode=markdown, text=escape_markdown(text), **kwargs)


def reply_message(update, text, **kwargs):
    try:
        get_message(update).reply_text(text=text, parse_mode=markdown, **kwargs)
    except api_error.TelegramError as tg_error:
        logger.info('Probably a wrong markup. Will escape characters and retry reply_text. Error: {}'.
                    format(tg_error.message))
        get_message(update).reply_text(text=escape_markdown(text), parse_mode=markdown, **kwargs)


def start(bot, update):
    del_update_and_message(update)
    if get_chat(update).type != models.Chat.CHANNEL:
        if get_chat(update).type != models.Chat.PRIVATE:
            message = 'Hi, My work is to help you forward messages from one chat to ' \
                      'another, You can setup auto forwarding using /setAutoForward in a private chat with me. ' \
                      'To do this you have to get the chat secret key from the chat administrators. ' \
                      'Use /help if you need info about my commands and /rules to read the /rules'

        else:
            message = 'Hi, My work is to help you forward messages from one chat'\
                      ' to the other, This is your secret key for use in forwarding messages'\
                      ' to my chat with you: {}. Use /help if you forget anything '\
                      .format(get_or_none(models.Chat, id=get_chat(update).id).identifier)

        send_message(bot, get_message(update).chat_id, text=message)


def help_command(bot, update):
    del_update_and_message(update)
    help_text = 'Here are a list of my commands: Use\n' \
                '/rules to read about the rules of auto forwarding' \
                '(strongly recommended before setting up forwarding)\n'\
                '/setautoforward to initiate the process of setting up auto forwarding \n' \
                '/delautoforward to initiate deletion of an auto forwarding \n'\
                '/cancel to terminate an ongoing process \n' \
                '/help to get the list of commands and their descriptions \n' \
                '/getsecretkey to get the secret key of your chat (needed for setting up auto forwarding)'
    bot.send_message(get_message(update).chat_id, text=help_text)


def rules(bot, update):
    del_update_and_message(update)
    forward_rules =  'These are the rules, restrictions and guidelines of setting up auto forwarding: \n\n' \
                    '1. Forwarding can only be setup in between chats that I have been added in \n'\
                    '2. For security and privacy purposes, people cannot set forwarding from a chat or to a chat ' \
                    'without the permission of at least one of the admins of the chats. For that purpose each ' \
                    'chat where I am added has a secret key which will be sent to the admins. To set forwarding, ' \
                    'you need to get the keys of both the sending chat and the receiving chat \n' \
                    '3. As a result of Telegrams\'s privacy policies I cannot send private messages to people ' \
                    'who have not initiated a conversation with me, so I cannot send the secret key to admins who ' \
                    'do not have a private chat with me. It is highly recommended that the admins themselves ' \
                    'add me to the chats and send me a private message before doing that.\n' \
                    '4. For channels, it is a bit tricky. The admins can only receive their secret keys after ' \
                    'one post has been made from the time I was added \n' \
                    '5. The only way to add me to channels is to add me as an admin (general Telegram rule)\n' \
                    '6. Forwarding can only be set to private chats (with me) and not from it \n' \
                    '7. A chat cannot receive forwarding if it is already sending out to another chat ' \
                    '(to prevent circular forwarding and loops)\n' \
                    '8. A chat can receive many forwardings (from more than 1 chat) or send many ' \
                    '(to more than one chat)\n' \
                    '9. You can set a language to translate all the text to when forwarding. I currently ' \
                    'support translations to English, Russian, Spanish, Chinese, French, Arabic, German and Hindi. ' \
                    'More will be added later if needed. Of course You can choose `None` to forward ' \
                    'without translations\n' \
                    '10. An auto forwarding can only be deleted either ny the person who set it up or one ' \
                    'of the admins of the chats involved\n' \
                    '11. Forwarding can only be setup and deleted in a private chat (else the keys would be leaked)\n'\
                    '12. If I am added to a chat and an auto forwarding is not set after some number of messages ' \
                    'I will leave the chat. This is to reduce the workload of having to handle many messages. ' \
                    'You can add me again when you need me. The number of messages are {} for channels, {} for ' \
                    'supergroups and {} for groups \n' \
                    '13. When all the forwardings a chat is involved in are deleted I will also leave. But again you ' \
                    'can always add me back to the chat. \n\n' \
                    'That is all for now. I hope you have fun working with me'.format(timeouts[models.Chat.CHANNEL],
                                                                                      timeouts[models.Chat.SUPERGROUP],
                                                                                      timeouts[models.Chat.GROUP])
    reply_message(update, text=forward_rules)


def on_add(bot, update):
    del_update_and_message(update)
    api_chat = get_chat(update)
    chat = get_or_none(models.Chat, id=api_chat.id)
    chat.extra_fields['left'] = False
    chat.save()
    if chat.type != models.Chat.PRIVATE:
        for admin in api_chat.get_administrators():
            if not admin.user.username.endswith('bot'):
                if get_or_none(models.User, id=admin.user.id):
                    if not chat.extra_fields['enabled']:
                        chat.extra_fields['enabled'] = True
                        chat.save()
                    group_type = api_chat.type
                    send_message(bot,
                                 admin.user.id,
                                 text='Hello, I was added to the {}: `{}` where you are an admin. '
                                      'For security purposes I only allow forwarding from groups '
                                      'if one of the admins approve of it. This is the secret key '
                                      'of your {}: {}. It will enable users to set forwarding to '
                                      'and from your {}. Only give this key to those you have '
                                      'allowed to do so. Have a nice day:)'
                                      .format(group_type, chat.title,
                                              group_type, chat.identifier,
                                              group_type))


def on_remove(bot, update):
    del_update_and_message(update)
    chat = get_or_none(models.Chat, id=get_chat(update).id)
    outgoing = AutoForward.objects.filter(forwarder__id=chat.id)
    outgoing.delete()
    incoming = AutoForward.objects.filter(receiver__id=chat.id)
    incoming.delete()
    if chat.type == models.Chat.PRIVATE:
        user = get_or_none(models.User, id=get_message(update).from_user.id)
        if user:
            user.delete()
    logger.info('{} has been removed from the {} {}'.format(fd_username, chat.type, chat.title))
    chat.extra_fields['message_counter'] = 0
    chat.extra_fields[enabled] = False
    chat.extra_fields['left'] = True
    chat.save()
    # chat.delete()

# AUTO FOWARDING

SENDER, RECEIVER, LANGUAGE, = range(3)


def set_auto_forward(bot, update):
    del_update_and_message(update)
    logger.debug('starting the auto forwarding')
    if get_chat(update).type != models.Chat.CHANNEL:
        if get_chat(update).type != models.Chat.PRIVATE:
            reply_message(update, text='Sorry, this command can only be used in a private chat')
            return ConversationHandler.END
        else:
            reply_message(update,
                          text='Hello! It is good you want to set up auto forwarding. I hope you have read the rules '
                               'with /rules. If not please read them before starting the setup'
                               'Send /cancel to terminate the process.\n\n'
                               'Please give me the secret key of the chat(group, supergroup or channel) '
                               'you want to forward from. '
                               'You can get it from one of the admins if you don\'t have it. Remember I have to be '
                               'added to the chat (preferably by '
                               'one of the administrators) to be able to forward messages to and from it.',
                )
        return SENDER
    return ConversationHandler.END


def set_sender(bot, update, user_data):
    del_update_and_message(update)
    try:
        sender = get_or_none(models.Chat, identifier=get_message(update).text)
        if sender is None or not sender.extra_fields[enabled]:
            reply_message(update,
                          text="The key you provided does not exist, "
                               "please check that it is correct and I am still in the chat")
            return SENDER
        if sender.type == models.Chat.PRIVATE:
            reply_message(update,
                          text="The key you provided belongs to a private chat. Forwarding cannot "
                               "be set from my users' private chat with me. You can only forward to them. "
                               "please enter another chat's secret key or use /cancel to terminate ")
            return SENDER
        forwardings = AutoForward.objects.filter(receiver=sender)
        if len(forwardings) > 0:
            reply_message(update,
                          text="Unfortunately, this chat is already receiving auto "
                               "forwards from another chat. In order to prevent circular "
                               "forwardings, I do not allow a chat to send and receive forwards "
                               "simultaneously, please enter another chat's secret key or "
                               "use /cancel to terminate the setup. Later you can use /rules to read more "
                               "about the auto forwarding rules")
            return SENDER

        user_data['sender_id'] = sender.id
        reply_message(update, text="Great!, now enter the secret key of the chat(user, group, supergroup or "
                                   "channel) you want me to forward the messages to.")
        return RECEIVER
    except Exception as ex:
        logger.error(ex.message)
        reply_message(update, text="Oops! Please enter the key correctly")
        return SENDER

lang_choices = list(Languages.choices())
lang_choices.sort()


def set_receiver(bot, update, user_data):
    del_update_and_message(update)
    logger.debug('set_receiver called')
    reply_keyboard = [[label for label, name in lang_choices]]
    try:
        receiver = get_or_none(models.Chat, identifier=get_message(update).text)
        if receiver is None or not receiver.extra_fields[enabled]:
            reply_message(update,
                          text="Unfortunately, the key you provided does not exist, "
                               "please check that the key is correct and that I'm still in the chat. "
                               "You can ask the admins of the chat")
            return RECEIVER
        if receiver.id == user_data['sender_id']:
            reply_message(update, text="Oops! The receiving chat cannot be the same as the as the forwarding chat"
                                       "please enter the correct secret key")
            return RECEIVER
        forwardings = AutoForward.objects.filter(forwarder=receiver)
        if len(forwardings) > 0:
            reply_message(update,
                          text="Unfortunately, this chat is already sending auto "
                               "forwards to another chat. In order to prevent circular "
                               "forwardings, I do not allow a chat to send and receive forwards "
                               "simultaneously, please enter another chat's secret key or "
                               "use /cancel to terminate the setup. Later you can use /rules to read more "
                               "about the auto forwarding rules")
            return RECEIVER
        forwardings = AutoForward.objects.filter(receiver=receiver, forwarder__id=user_data['sender_id'])
        if len(forwardings) > 0:
            reply_message(update,
                          text="Oops! There is already an auto forwarding between these two chats. "
                               "Another one cannot be set until the existing one is deleted. Please use "
                               "/cancel to cancel or enter another chat's secret key to "
                               "continue the setup")
            return RECEIVER
        user_data['receiver_id'] = receiver.id
        reply_message(update,
                      text="We are almost done, now you just have to choose a language to "
                           "translate the messages to, before forwarding. Choose None if you "
                           "don't need translating the messages",
                           reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return LANGUAGE
    except Exception as ex:
        logger.error(ex.message)
        reply_message(update, text="Oops! Please enter the key correctly")
        return RECEIVER


def set_lang(bot, update, user_data):
    del_update_and_message(update)
    if not get_message(update).text in [label for label, name in lang_choices]:
        reply_message(update, text='Easy there my friend! Please, select only options in the keyboard')
        return LANGUAGE
    user_data['language'] = get_message(update).text
    forwarding = None
    try:
        sender = get_or_none(models.Chat, id=user_data['sender_id'])
        receiver = get_or_none(models.Chat, id=user_data['receiver_id'])
        creator = get_or_none(models.User, id=get_message(update).from_user.id)
        header = '`Forwarded from {}`'.format(sender.username) if sender.username else \
            '`Forwarded from {}`'.format(sender.title)
        forwarding = AutoForward.objects.create(forwarder=sender, receiver=receiver,
                                                creator=creator, lang=user_data['language'],
                                                message_header=header)
        if forwarding:
            logger.info('Auto forwarding has been set {} to {}'.format(sender.title, receiver.title))
            user_data = {}
            reply_message(update,
                          text="Congratulations! Your auto forwarding has been set and"
                               " should now be up and running!", reply_markup=ReplyKeyboardRemove())
    except Exception as ex:
        logger.error(ex.message)
        if not forwarding:
            reply_message(update, text="Oops! Something went wrong, please try again later!")

    return ConversationHandler.END

# Auto Forwarding Deletion

DEL_SENDER, DEL_RECEIVER = range(5, 7)


def delete_auto_forwarding(bot, update):
    del_update_and_message(update)
    logger.debug('starting the auto forwarding deletion')
    if get_chat(update).type != models.Chat.CHANNEL:
        if get_chat(update).type != models.Chat.PRIVATE:
            reply_message(update,
                          text='Sorry, this command can only be used in a private chat!')
            return ConversationHandler.END
        else:
            reply_message(update,
                          text='Hello! It will just take a few steps to disable the auto forwarding. '
                               'Remember that you can '
                               'only disable an auto forwarding you setup by yourself or if you are an '
                               'admin in a group '
                               'involved in the auto forwarding. Send /cancel to cancel the process.\n\n'
                               'Please give me the secret key of the chat(group, supergroup or channel) '
                               'which is being forwarded from.')
            return DEL_SENDER
    return ConversationHandler.END


def del_sender(bot, update, user_data):
    del_update_and_message(update)
    try:
        sender = get_or_none(models.Chat, identifier=get_message(update).text)
        if sender is None:
            reply_message(update,
                          text="The key you provided does not exist, "
                               "please check that it is correct")
            return DEL_SENDER
        user_data['sender_id'] = sender.id
        reply_message(update,
                      text="Great, now enter the secret key of the chat(user, group, supergroup "
                           "or channel) which is being forwarding to ")
        return DEL_RECEIVER
    except Exception as ex:
        logger.error(ex.message)
        reply_message(update, text="Oops! Please enter the key correctly")
        return DEL_SENDER


def del_receiver(bot, update, user_data):
    del_update_and_message(update)
    logger.debug('del_receiver called')
    try:
        sender = get_or_none(models.Chat, id=user_data['sender_id'])
        receiver = get_or_none(models.Chat, identifier=get_message(update).text)
        if receiver is None:
            reply_message(update,
                          text="Unfortunately, the key you provided does not exist, "
                               "please check that the key is correct")
            return DEL_RECEIVER
        forwarding = get_or_none(AutoForward, forwarder__id=user_data['sender_id'],
                                 receiver__id=receiver.id)
        if not forwarding:
            reply_message(update,
                          text="Oops! There is no auto forwarding set between these two chats, "
                               "ensure that both have an active auto forwarding and try again later.")
            return ConversationHandler.END
        authorzed = False
        if forwarding.creator.id != get_message(update).from_user.id:
            api_sender = APIChat(sender.id, sender.type, bot=bot)
            api_receiver = APIChat(receiver.id, receiver.type, bot=bot)
            if api_sender.type != models.Chat.PRIVATE:
                if get_message(update).from_user.id not in [admin.user.id for admin in api_sender.get_administrators()]:
                    if api_receiver.type != models.Chat.PRIVATE:
                        if get_message(update).from_user.id in [admin.user.id for admin in
                                                                api_receiver.get_administrators()]:
                            authorzed = True
                    elif api_receiver.id == get_message(update).from_user.id:
                        authorzed = True
                else:
                    authorzed = True
            elif api_sender.id == get_message(update).from_user.id:
                authorzed = True
        else:
            authorzed = True
        if not authorzed:
            reply_message(update,
                          text="Unfortunately you are neither the creator of this auto forwarding "
                               "or an admin in one of the chats involved. Please request deactivation from "
                               "the admin or the auto forwarding creator")
            return ConversationHandler.END
        else:
            forwarding.delete()
            send_message(bot, get_message(update).chat_id, text="forwarding has been deleted successfully.")
            logger.info("forwarding from {} to {} has been deleted".format(sender.title, receiver.title))
            forwardings_rec = AutoForward.objects.filter(receiver=receiver)
            forwardings_send = AutoForward.objects.filter(forwarder=sender)
            if receiver.type != models.Chat.CHANNEL and receiver.type != models.Chat.PRIVATE:
                text = 'The auto forwarding from {} to this {} has been deleted, ' \
                       'so I will no longer forward message from there.'.format(sender.title, receiver.type)
                if len(forwardings_rec) == 0:
                    text += ' Since there are no more auto forwardings involving this chat, I will now '\
                            'leave. If you need me again, just holla at me (@{}) and add me '\
                            'me to the chat. It was fun having you all!'.format(fd_username)
                send_message(bot, chat_id=receiver.id, text=text)
            if receiver.type != models.Chat.PRIVATE:
                if len(forwardings_rec) == 0:
                    bot.leave_chat(receiver.id)
                    receiver.extra_fields['left'] = True
                    receiver.extra_fields['enabled'] = False
                    sender.extra_fields['message_counter'] = 0
                    receiver.save()
                    logger.info('{} has left the {} {}'.format(fd_username, receiver.type, receiver.title))
                    # receiver.delete()
                if len(forwardings_send) == 0:
                    bot.leave_chat(sender.id)
                    sender.extra_fields['left'] = True
                    sender.extra_fields['enabled'] = False
                    sender.extra_fields['message_counter'] = 0
                    sender.save()
                    logger.info('{} has left the {} {}'.format(fd_username, receiver.type, receiver.title))
                    # sender.delete()
            user_data = {}
            return ConversationHandler.END
    except Exception as ex:
        logger.error(ex.message)
        reply_message(update, text="Oops! Something went wrong, please try again later!")
        return RECEIVER


def cancel(bot, update, user_data):
    user_data = {}
    if get_chat(update).type == models.Chat.PRIVATE:
        reply_message(update,
                      text='Not to worry! We can try again sometime later.',
                      reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def forward(bot, forwarding, update):
    bot.forward_message(chat_id=forwarding.receiver.id,
                        from_chat_id=forwarding.forwarder.id,
                        message_id=get_message(update).message_id)
    if forwarding.forwarder.type != models.Chat.CHANNEL:
        extra_message = str(forwarding.message_header)
        send_message(bot, chat_id=forwarding.receiver.id, text=extra_message)


def forward_text(bot, update):
    del_update_and_message(update)
    forwardings = AutoForward.objects.filter(forwarder__id=get_chat(update).id)
    for forwarding in forwardings:
        if forwarding.enabled:
            if forwarding.lang == Languages.NONE.value:
                return forward(bot, forwarding, update)
            translator = Translator()
            heading = forwarding.message_header
            if update.message and update.message.from_user.username:
                heading = "`By` @{}".format(get_message(update).from_user.username) + "\n" + heading
            elif update.message:
                if update.message.from_user.last_name:
                    heading = "`By {} {}`".format(get_message(update).from_user.first_name,
                                                  get_message(update).from_user.last_name) + "\n" + heading
                else:
                    heading = "`By {}`".format(get_message(update).from_user.first_name) + "\n" + heading
            heading += '\n\n'
            text = heading + translator.translate(text=get_message(update).text,
                                                  lang_to=forwarding.lang)
            send_message(bot, forwarding.receiver.id, text=text)


def forward_others(bot, update):
    del_update_and_message(update)
    forwardings = AutoForward.objects.filter(forwarder__id=get_chat(update).id)
    for forwarding in forwardings:
        if forwarding.enabled:
            forward(bot, forwarding, update)

CHAT_TYPE, CHAT_USERNAME, CHAT_TITLE = range(11, 14)


def get_key(bot, update, user_data):
    del_update_and_message(update)
    reply_keyboard = [['public supergroup or public channel', 'private chat'],
                      ['private channel', 'private supergroup', 'private group']]
    if get_chat(update).type != models.Chat.CHANNEL:
        message = ''
        if get_chat(update).type != models.Chat.PRIVATE:
            message = 'Oops! This command can only be used in private chats'
            reply_message(update, text=message)
            return ConversationHandler.END
        else:
            user_data['types_keyboard'] = [chat_type for i in reply_keyboard for chat_type in i]
            reply_message(update, text='Please choose the chat type you want to get the key',
                          reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
            return CHAT_TYPE


def get_chat_type(bot, update, user_data):
    del_update_and_message(update)
    if not get_message(update).text in user_data['types_keyboard']:
        reply_message(update, text='Easy there my friend! Please, select only options in the keyboard')
        return CHAT_TYPE
    user_data['chat_type'] = get_message(update).text
    if user_data['chat_type'] == 'private chat':
        chat = get_or_none(models.Chat, id=get_chat(update).id)
        if chat:
            reply_message(update, text='The secret key for this chat is {}'.format(chat.identifier),
                          reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END
    if user_data['chat_type'] == 'public supergroup or public channel':
        reply_message(update, text='Awesome! now enter the username of your public channel or supergroup '
                                   'without the "@" symbol')
        return CHAT_USERNAME
    reply_message(update,
                  text='It is a bit tricky finding private groups, supergroups and channels '
                       'because they do not have unique usernames like the public ones do. '
                       'In any case, I am dedicated to bringing you my service in the best possible way '
                       'so I wil try and see if I can get your secret key \n\n'
                       'Please give me the title of your private group, supergroup or channel',
                  reply_markup=ReplyKeyboardRemove())
    return CHAT_TITLE


def get_username(bot, update, user_data):
    del_update_and_message(update)
    chat = get_or_none(models.Chat, username=get_message(update).text)
    if chat and not chat.extra_fields['left']:
        api_chat = APIChat(chat.id, chat.type, bot=bot)
        if get_message(update).from_user.id in [admin.user.id for admin in
                                                api_chat.get_administrators()]:
            reply_message(update, text='The secret key for your chat is {}'.format(chat.identifier))
            if not chat.extra_fields[enabled]:
                chat.extra_fields[enabled] = True
            return ConversationHandler.END
        else:
            reply_message(update, text='Sorry, you are not an admin in this chat so I cannot give '
                                       'you the chat\'s secret key. Please contact your admin to get the key.')
            return ConversationHandler.END

    reply_message(update, text='Oops! This username is not in the list of groups using my service. Are you sure you '
                               'it is correct? Make sure to remove the @ symbol. You can try entering the '
                               'username again or use /cancel to quit ')
    return CHAT_USERNAME


def get_title(bot, update, user_data):
    del_update_and_message(update)
    chat_type = user_data['chat_type'].split(' ')
    chats = models.Chat.objects.filter(title=get_message(update).text, type=chat_type[1])
    if chats and len(chats) == 1 and not chats.first().extra_fields['left']:
        chat = chats.first()
        api_chat = APIChat(chat.id, chat.type, bot=bot)
        if get_message(update).from_user.id in [admin.user.id for admin in
                                                api_chat.get_administrators()]:
            reply_message(update, text='Lucky! The secret key for your chat is {}'.format(chat.identifier))
            if not chat.extra_fields[enabled]:
                chat.extra_fields[enabled] = True
            return ConversationHandler.END
        else:
            reply_message(update, text='Sorry, you are not an admin in this chat so I cannot give '
                                       'you the chat\'s secret key. Please contact your admin to get the key.')
            return ConversationHandler.END

    reply_message(update, text='Unfortunately, I couldn\'t find your chat either because no chat using my service '
                               'has such title or there are many of them. Please contact my developer (@{}) '
                               'and I am sure he will help you find your chat key'.format(dev_username))
    return ConversationHandler.END


def unknown(bot, update):
    del_update_and_message(update)
    try:
        sender = get_or_none(models.Chat, id=get_chat(update).id)
        if sender.type != models.Chat.PRIVATE and sender.extra_fields['message_counter'] >= timeouts[sender.type]:
            if sender.type == models.Chat.GROUP or sender.type == models.Chat.SUPERGROUP:
                send_message(bot, sender.id, text='You have not setup any auto forwarding since you added me, so '
                                                  'I will leave because I\'m busy serving other chats. Just add me '
                                                  'back again when you need me (@{}) '.format(fd_username))
            bot.leave_chat(sender.id)
            sender.extra_fields['enabled'] = False
            sender.extra_fields['left'] = True
            sender.extra_fields['message_counter'] = 0
            sender.save()
            logger.info('{} has left the {} {}'.format(fd_username, sender.type, sender.title))
        elif not get_message(update).left_chat_member or \
                (get_message(update).left_chat_member and get_message(update).left_chat_member.username != fd_username):
                sender.extra_fields['message_counter'] += 1
                sender.save()

    except Exception as ex:
        logger.exception('an error occurred while processing an unknown message from {}: {}'
                         .format(get_chat(update).title if get_chat(update).title else get_chat(update).username,
                                 ex.message))


def error(bot, update, error_message):
    logger.error(error_message)
    if get_chat(update).type == models.Chat.PRIVATE:
        send_message(bot, get_chat(update).id, text='Sorry, an error occurred:( Try again later')


# this method will be called on start of application
def register(dispatcher):
    set_forward = GoodConversationHandler(
                entry_points=[CommandHandler('setautoforward', set_auto_forward)],

                states={
                    SENDER: [CustomRegexHandler('[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?'
                                                '[89ab][a-f0-9]{3}-?[a-f0-9]{12}\Z',
                                                set_sender, pass_user_data=True)],

                    RECEIVER: [CustomRegexHandler('[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?'
                                                  '[89ab][a-f0-9]{3}-?[a-f0-9]{12}\Z',
                                                  set_receiver, pass_user_data=True)],

                    LANGUAGE: [MessageHandler(Filters.text, set_lang, pass_user_data=True)],

                },

                fallbacks=[CommandHandler('cancel', cancel, pass_user_data=True)]
            )

    get_secret_key = GoodConversationHandler(
        entry_points=[CommandHandler('getsecretkey', get_key, pass_user_data=True)],

        states={
            CHAT_TYPE: [MessageHandler(Filters.text, get_chat_type, pass_user_data=True)],

            CHAT_USERNAME: [MessageHandler(Filters.text, get_username, pass_user_data=True)],

            CHAT_TITLE: [MessageHandler(Filters.text, get_title, pass_user_data=True)],

        },

        fallbacks=[CommandHandler('cancel', cancel, pass_user_data=True)]
    )

    del_forward = GoodConversationHandler(
        entry_points=[CommandHandler('delautoforward', delete_auto_forwarding)],

        states={
            DEL_SENDER: [CustomRegexHandler('[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?'
                                            '[89ab][a-f0-9]{3}-?[a-f0-9]{12}\Z',
                                            del_sender, pass_user_data=True)],

            DEL_RECEIVER: [CustomRegexHandler('[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?'
                                              '[89ab][a-f0-9]{3}-?[a-f0-9]{12}\Z',
                                              del_receiver, pass_user_data=True)],
        },

        fallbacks=[CommandHandler('cancel', cancel, pass_user_data=True)]
    )

    dispatcher.add_handler(MessageHandler((ForwardMessageFilters.added(fd_username) |
                                           ForwardMessageFilters.channel_added), on_add))
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('help', help_command))
    dispatcher.add_handler(CommandHandler('rules', rules))
    dispatcher.add_handler(set_forward)
    dispatcher.add_handler(get_secret_key)
    dispatcher.add_handler(del_forward)
    dispatcher.add_handler(MessageHandler(ForwardMessageFilters.text_forwardings, forward_text))
    dispatcher.add_handler(MessageHandler(ForwardMessageFilters.other_forwardings, forward_others))
    dispatcher.add_handler(MessageHandler(ForwardMessageFilters.removed(fd_username), on_remove))
    dispatcher.add_handler(MessageHandler(Filters.all, unknown))
    dispatcher.add_error_handler(error)

# Django Telegram Bot settings
token = settings.SECRETS['bot']['token']
try:
    mybot = models.Bot.objects.get(token=token)
    mybot.set_dispatcher(register)
except Exception as e:
    logger.exception('An error occurred while trying to fetch the bot, please ensure that the bot model has'
                     'been created and you have created a bot with the corresponding token')
models.set_webhook_url(token, '/forwarder/api/webhook/'+token)
