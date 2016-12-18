# coding=utf-8
from __future__ import unicode_literals

try:
    print ('Trying import local.py settings...')
    from .local import *  # noqa
except ImportError:
    print ('Trying import development.py settings...')
    from .development import *  # noqa
