# coding=utf-8
from __future__ import unicode_literals

import logging

from telegram.ext import Dispatcher

logger = logging.getLogger(__file__)

class DjangoDispatcher(Dispatcher):

    def __init__(self, bot):
        super(Dispatcher, self).__init__()
        self.bot = bot

        self.handlers = {}
        """:type: dict[int, list[Handler]"""
        self.groups = []
        """:type: list[int]"""
        self.error_handlers = []

        self.logger = logging.getLogger(__name__)

    def start(self):
        self.logger.warning('DjangoDispatcher do not need start or thread.')