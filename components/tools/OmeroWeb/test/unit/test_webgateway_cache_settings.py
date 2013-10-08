# -*- coding: utf-8 -*-
"""
    Copyright 2007-2013 Glencoe Software, Inc. All rights reserved.
    Use is subject to license terms supplied in LICENSE.txt

    Django settings for the test_webgateway_cache unit tests.
"""

import os
from omero.util import temp_files

CACHE_ROOT = temp_files.create_path('django_cache', folder=True)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(CACHE_ROOT, 'default'),
    }
}
