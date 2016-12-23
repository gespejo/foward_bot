# coding=utf-8
from __future__ import unicode_literals

from .base import *  # noqa


DEBUG = True

SITE_ID = 3

ALLOWED_HOSTS = [".ngrok.io",
                 "localhost"]

SECURE_SSL_REDIRECT = False

MICROBOT_WEBHOOK_DOMAIN = "https://ken-dev.ngrok.io"


INSTALLED_APPS.append("sslserver")

APPEND_SLASH = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'foward_bot',
        'USER': 'kenneth',
        'PASSWORD': 'nedutext',
        'HOST': 'localhost',
        'PORT': '',
    }
}

