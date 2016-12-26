# coding=utf-8
from __future__ import unicode_literals

from django.contrib import admin

from .models import *

#
admin.site.register(User)
admin.site.register(Update)
admin.site.register(Bot)
admin.site.register(Message)
admin.site.register(Chat)
