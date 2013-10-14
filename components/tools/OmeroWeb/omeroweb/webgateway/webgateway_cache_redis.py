#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Experiemental webgateway cache rewrite using redis
# 
# Copyright (c) 2008, 2013 Glencoe Software, Inc. All rights reserved.
# 
# This software is distributed under the terms described by the LICENCE file
# you can find at the root of the distribution bundle, which states you are
# free to use it only for non commercial purposes.
# If the file is missing please request a copy by contacting
# jason@glencoesoftware.com.
#
# Authors: Carlos Neves <carlos(at)glencoesoftware.com>
#          Sam Hart <sam(at)glencoesoftware.com>

from django.conf import settings

import omero
import logging
import redis

logger = logging.getLogger(__name__)

class WebGatewayeCacheRedis(object):
    """
    Experiemental rewrite of WebGatewayeCache using Redis as the caching
    backend.
    """

    def __init__(self):
        self._redis_host = getattr(settings, 'REDIS_HOST', 'localhost')
        self._redis_port = getattr(settings, 'REDIS_PORT', 6379)
        self._redis_db = getattr(settings, 'REDIS_DB', 0)
        self._default_timout = getattr(settings, 'REDIS_DEFAULT_TIMEOUT', 60)

        self._redis = redis.StrictRedis(host=self._redis_host, \
            port=self._redis_port, db=self._redis_db)

    def tryLock(self):
        """
        Kept around for legacy WebGatewayeCache support
        """
        return True

    def handleEvent (self, client_base, e):
        """
        Handle one event from blitz.onEventLogs.

        Meant to be overridden, this implementation just logs.
        
        @param client_base:     TODO: docs!
        @param e:       
        """
        logger.debug('## %s#%i %s user #%i group #%i(%i)' % (e.entityType.val,
                                                             e.entityId.val,
                                                             e.action.val,
                                                             e.details.owner.id.val,
                                                             e.details.group.id.val,
                                                             e.event.id.val))

    def eventListener (self, client_base, events):
        """
        handle events coming our way from blitz.onEventLogs.
        
        Because all processes will be listening to the same events, we use a simple file
        lock mechanism to make sure the first process to get the event will be the one
        handling things from then on.
        
        @param client_base:     TODO: docs!
        @param events:
        """
        for e in events:
            self.handleEvent(client_base, e)

    def clear (self):
        """
        Currently a no-op.
        """
        pass

    def invalidateObject (self, client_base, user_id, obj):
        """
        Invalidates all caches for this particular object
        
        @param client_base:     The server_id
        @param user_id:         OMERO user ID to partition caching upon
        @param obj:             The object wrapper. E.g. L{omero.gateway.ImageWrapper}
        """
        
        if obj.OMERO_CLASS == 'Image':
            self.clearImage(None, client_base, user_id, obj)
        else:
            logger.debug('unhandled object type: %s' % obj.OMERO_CLASS)
            self.clearJson(client_base, obj)


    ##
    # Thumb

    def _thumb_key(self, client_base, user_id, iid, size):
        """
        Generates the hash and string key for caching the thumbnail.

        @param client_base:     server-id, forms stem of the key
        @param user_id:         OMERO user ID to partition caching upon
        @param iid:             image ID
        @param size:            size of the thumbnail - tuple. E.g. (100,)

        @return (hash_string, key_string)
        """
        pre = str(iid)[:-4]
        hash_string = 'thumb_user_%s'client_base
        key_string = ''
        if len(pre) == 0:
            pre = '0'
        if size is not None and len(size):
            key_string ='%s/%s/%s/%s' % (pre, str(iid), user_id, 'x'.join([str(x) for x in size]))
        else:
            key_string ='%s/%s/%s' % (pre, str(iid), user_id)

        return (hash_string, key_string)

    def setThumb(self, r, client_base, user_id, iid, obj, size=()):
        """
        Puts thumbnail into cache. 
        
        @param r:               for cache key - Not used? 
        @param client_base:     server_id for cache key
        @param user_id:         OMERO user ID to partition caching upon
        @param iid:             image ID for cache key
        @param obj:             Data to cache
        @param size:            Size used for cache key. Tuple
        """
        
        (h,k) = self._thumbKey(r, client_base, user_id, iid, size)
        self._redis.hset(h,k,obj)
        if self._redis.ttl(h) < 0:
            self._redis.expire(h, self._default_timout)
        return True

    def getThumb(self, r, client_base, user_id, iid, size=()):
                """
        Gets thumbnail from cache. 
        
        @param r:               for cache key - Not used? 
        @param client_base:     server_id for cache key
        @param user_id:         OMERO user ID to partition caching upon
        @param iid:             image ID for cache key
        @param size:            Size used for cache key. Tuple
        @return:                Cached data or None
        @rtype:                 String
        """
        (h,k) = self._thumbKey(r, client_base, user_id, iid, size)
        r = self._redis.hget(h,k)
        if r is None:
            logger.debug('  fail: %s' % k)
        else:
            logger.debug('cached: %s' % k)
        return r
        