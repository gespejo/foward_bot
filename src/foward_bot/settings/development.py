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

YANDEX_API_KEY = 'trnsl.1.1.20161226T211040Z.9e963380a71a1645.a935c43983b6417a3735c8090caf01401b1a0fbe'

# APPEND_SLASH = False

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


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
        },
        'simple': {
            'format': '[%(name)s] %(levelname)s: %(message)s'
        }
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'filters': ['require_debug_true'],
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(BASE_DIR, '../../log', 'forward_bot.log'),
            'when': 'd',
            'backupCount': 7,
            'formatter': 'verbose',
            'filters': ['require_debug_false'],
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        # 'django.request': {
        #     'level': 'ERROR',
        #     'handlers': ['mail_admins'],
        #     'propagate': False,
        # },
        # 'foward_bot': {
        #     'level': 'DEBUG',
        #     'handlers': ['console'],
        #     'propagate': True,
        # },
    },
}

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'handlers': {
#         'console': {
#             'class': 'logging.StreamHandler',
#         },
#     },
#     'loggers': {
#         'django': {
#             'handlers': ['console'],
#             'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
#         },
#     },
# }

