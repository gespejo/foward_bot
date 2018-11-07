# coding=utf-8
from __future__ import unicode_literals

from django.contrib import admin

from .models import *


class ChatAdmin(admin.ModelAdmin):

    list_display = ('identifier', 'title', 'username', 'first_name', 'last_name')
    search_fields = ('title', 'username', 'first_name', 'last_name')


admin.site.register(User)
admin.site.register(Update)
admin.site.register(Bot)
admin.site.register(Message)
admin.site.register(Chat, ChatAdmin)
