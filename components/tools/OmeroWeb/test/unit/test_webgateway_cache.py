# -*- coding: utf-8 -*-
"""
   Copyright 2007-2013 Glencoe Software, Inc. All rights reserved.
   Use is subject to license terms supplied in LICENSE.txt

"""

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'unit.test_webgateway_cache_settings'

import unittest

try:
    import redis
    from omeroweb.webgateway.webgateway_cache_redis import WebGatewayCacheRedis as WebGatewayCache
except:
    from omeroweb.webgateway.webgateway_cache_redis import WebGatewayCacheNull as WebGatewayCache

import django
import omero
from omero.gateway.scripts.testdb_create import *

class TestWebGatewayCache(unittest.TestCase):

    def setUp(self):
        self.cache = WebGatewayCache()
        class r:
            def __init__ (self):
                self.REQUEST = {'c':'1|292:1631$FF0000,2|409:5015$0000FF','m':'c', 'q':'0.9'}
            def new (self, q):
                rv = self.__class__()
                rv.REQUEST.update(q)
                return rv
        self.request = r()

    def testSetThumb(self):
        self.cache.setThumb(None, 'omero', 1L, 1L, 'abcdef', (64, 64))

    def testClear(self):
        self.cache.clear()

    def testThumbCache (self):
        uid = 123
        assert self.cache.getThumb(self.request, 'test', uid, 1) is None
        self.cache.setThumb(self.request, 'test', uid, 1, 'thumbdata')
        assert self.cache.getThumb(self.request, 'test', uid, 1) == 'thumbdata',\
               'Thumb not properly cached (%s)' % self.cache.getThumb(self.request, 'test', uid, 1)
        self.cache.clearThumb(self.request, 'test', uid, 1)
        assert self.cache.getThumb(self.request, 'test', uid, 1) is None
        # Make sure clear() nukes this
        self.cache.setThumb(self.request, 'test', uid, 1, 'thumbdata')
        assert self.cache.getThumb(self.request, 'test', uid, 1) == 'thumbdata', 'Thumb not properly cached'
        self.cache.clear()

    def testImageCache (self):
        uid = 123
        # Also add a thumb, a split channel and a projection, as it should get deleted with image
        preq = self.request.new({'p':'intmax'})
        assert self.cache.getThumb(self.request, 'test', uid, 1) is None
        self.cache.setThumb(self.request, 'test', uid, 1, 'thumbdata')
        assert self.cache.getThumb(self.request, 'test', uid, 1) == 'thumbdata'
        img = omero.gateway.ImageWrapper(None, omero.model.ImageI(1,False))
        assert self.cache.getImage(self.request, 'test', img, 2, 3) is None
        self.cache.setImage(self.request, 'test', img, 2, 3, 'imagedata')
        assert self.cache.getImage(self.request, 'test', img, 2, 3) == 'imagedata'
        assert self.cache.getImage(preq, 'test', img, 2, 3) is None
        self.cache.setImage(preq, 'test', img, 2, 3, 'imagedata')
        assert self.cache.getImage(preq, 'test', img, 2, 3) == 'imagedata'
        assert self.cache.getSplitChannelImage(self.request, 'test', img, 2, 3) is None
        self.cache.setSplitChannelImage(self.request, 'test', img, 2, 3, 'imagedata')
        assert self.cache.getSplitChannelImage(self.request, 'test', img, 2, 3) == 'imagedata'
        self.cache.clearImage(self.request, 'test', uid, img)
        assert self.cache.getImage(self.request, 'test', img, 2, 3) is None
        assert self.cache.getSplitChannelImage(self.request, 'test', img, 2, 3) is None
        assert self.cache.getImage(preq, 'test', img, 2, 3) is None
        assert self.cache.getThumb(self.request, 'test', uid, 1) is None
        # The exact same behaviour, using invalidateObject
        self.cache.setThumb(self.request, 'test', uid, 1, 'thumbdata')
        assert self.cache.getThumb(self.request, 'test', uid, 1) == 'thumbdata'
        self.cache.setImage(self.request, 'test', img, 2, 3, 'imagedata')
        assert self.cache.getImage(self.request, 'test', img, 2, 3) == 'imagedata'
        assert self.cache.getImage(preq, 'test', img, 2, 3) is None
        self.cache.setImage(preq, 'test', img, 2, 3, 'imagedata')
        assert self.cache.getImage(preq, 'test', img, 2, 3) == 'imagedata'
        assert self.cache.getSplitChannelImage(self.request, 'test', img, 2, 3) is None
        self.cache.setSplitChannelImage(self.request, 'test', img, 2, 3, 'imagedata')
        assert self.cache.getSplitChannelImage(self.request, 'test', img, 2, 3) == 'imagedata'
        self.cache.invalidateObject('test', uid, img)
        assert self.cache.getImage(self.request, 'test', img, 2, 3) is None
        assert self.cache.getSplitChannelImage(self.request, 'test', img, 2, 3) is None
        assert self.cache.getImage(preq, 'test', img, 2, 3) is None
        assert self.cache.getThumb(self.request, 'test', uid, 1) is None
        # Make sure clear() nukes this
        assert self.cache.getImage(self.request, 'test', img, 2, 3) is None
        self.cache.setImage(self.request, 'test', img, 2, 3, 'imagedata')
        assert self.cache.getImage(self.request, 'test', img, 2, 3) == 'imagedata'

    def testJsonCache (self):
        uid = 123
        ds = omero.gateway.DatasetWrapper(None, omero.model.DatasetI(1,False))
        assert self.cache.getDatasetContents(self.request, 'test', ds) is None
        self.cache.setDatasetContents(self.request, 'test', ds, 'datasetdata')
        assert self.cache.getDatasetContents(self.request, 'test', ds) == 'datasetdata'
        self.cache.clearDatasetContents(self.request, 'test', ds)
        assert self.cache.getDatasetContents(self.request, 'test', ds) is None
        # The exact same behaviour, using invalidateObject
        assert self.cache.getDatasetContents(self.request, 'test', ds) is None
        self.cache.setDatasetContents(self.request, 'test', ds, 'datasetdata')
        assert self.cache.getDatasetContents(self.request, 'test', ds) == 'datasetdata'
        self.cache.invalidateObject('test', uid, ds)
        assert self.cache.getDatasetContents(self.request, 'test', ds) is None
        # Make sure clear() nukes this
        assert self.cache.getDatasetContents(self.request, 'test', ds) is None
        self.cache.setDatasetContents(self.request, 'test', ds, 'datasetdata')
        assert self.cache.getDatasetContents(self.request, 'test', ds) == 'datasetdata'

        self.cache.clear()
