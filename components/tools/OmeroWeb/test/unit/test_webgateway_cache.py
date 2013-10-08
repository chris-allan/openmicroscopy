# -*- coding: utf-8 -*-
"""
   Copyright 2007-2013 Glencoe Software, Inc. All rights reserved.
   Use is subject to license terms supplied in LICENSE.txt

"""

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'unit.test_webgateway_cache_settings'

import unittest
from omeroweb.webgateway.webgateway_cache import WebGatewayCache
import django

class TestWebGatewayCache(unittest.TestCase):

    def setUp(self):
        self.cache = WebGatewayCache()

    def testSetThumb(self):
        self.cache.setThumb(None, 'omero', 1L, 1L, 'abcdef', (64, 64))

    def testClear(self):
        self.cache.clear()

