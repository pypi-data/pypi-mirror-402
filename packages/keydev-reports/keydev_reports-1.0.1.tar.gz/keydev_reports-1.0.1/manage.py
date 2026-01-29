#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import sys
import django
import os
from django.conf import settings
from django.core.management import execute_from_command_line

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append('..')

settings.configure(
    DEBUG=True,
    ALLOWED_HOSTS=['localhost'],
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    },
    INSTALLED_APPS=('keydev_reports',),
    USE_TZ=True,
    SECRET_KEY='test-secret-key-for-testing',
    # ROOT_URLCONF='keydev_reports.urls',
)

django.setup()
execute_from_command_line(sys.argv)
