#!/usr/bin/env python

import sys
import django

from django.conf import settings
from django.test.runner import DiscoverRunner

settings.configure(DEBUG=True,
    DATABASES={
        'default':{
            'ENGINE':'django.db.backends.sqlite3',
        }
    },
    ROOT_URLCONF='flowr.urls',
    INSTALLED_APPS=(
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.admin',
        'flowr',
        'flowr.tests',
    ),
)

django.setup()
runner = DiscoverRunner(verbosity=1)
failures = runner.run_tests(['flowr.tests'])
if failures:
    sys.exit(failures)
