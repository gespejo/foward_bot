# coding=utf-8
from __future__ import unicode_literals
import dj_database_url

from .base import *  # noqa

DEBUG = False

SITE_ID = 3

ALLOWED_HOSTS = SECRETS['allowed_hosts']['production']

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# SECURE_SSL_REDIRECT = False
#
#
# INSTALLED_APPS.append("sslserver")
# INSTALLED_APPS.append('debug_toolbar')
# MIDDLEWARE_CLASSES.insert(
#         MIDDLEWARE_CLASSES.index('django.middleware.common.CommonMiddleware') + 1,
#         'debug_toolbar.middleware.DebugToolbarMiddleware',
#     )


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': SECRETS['database']['production']['NAME'],
        'USER': SECRETS['database']['production']['USER'],
        'PASSWORD': SECRETS['database']['production']['PASSWORD'],
        'HOST': SECRETS['database']['production']['HOST'],
        'PORT': SECRETS['database']['production']['PORT'],
    }
}

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

STATIC_ROOT = os.path.join(BASE_DIR, "static/")


MESSAGE_TIMEOUTS = {
    'channel': 50,
    'group': 200,
    'supergroup': 500
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
        # '': {
        #     'handlers': ['file'],
        #     'level': 'ERROR',
        #     'propagate': False,
        # },
        'django.request': {
            'level': 'ERROR',
            'handlers': ['mail_admins'],
            'propagate': False,
        },
        'foward_bot': {
            'level': 'INFO',
            'handlers': ['file'],
            'propagate': True,
        },
        'telegram': {
            'level': 'ERROR',
            'handlers': ['file'],
            'propagate': True
    },
        }
}



