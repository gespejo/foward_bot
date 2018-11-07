# coding=utf-8
from __future__ import unicode_literals

from django.contrib import admin
from .models import AutoForward


class AutoForwardAdmin(admin.ModelAdmin):
    list_display = ('forwarder', 'receiver', 'enabled', 'creator', 'lang')
    search_fields = (
        'forwarder__title',
        'forwarder__username',
        'forwarder__first_name',
        'forwarder__last_name',
        'receiver__title',
        'receiver__username',
        'receiver__first_name',
        'receiver__last_name',
        'creator__username',
        'creator__first_name',
        'creator__last_name',
    )


admin.site.register(AutoForward, AutoForwardAdmin)

