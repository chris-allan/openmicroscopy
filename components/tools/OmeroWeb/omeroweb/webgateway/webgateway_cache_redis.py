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
        self._default_timeout = getattr(settings, 'REDIS_DEFAULT_TIMEOUT', 60)

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

    def _cache_set(self, h, k, obj, timeout=self._default_timeout):
        """
        Sets the cache.

        @param h:               The hash_key for the cache
        @param k:               The key for the cache
        @param obj:             The object to cache
        @param timeout:         The timeout for the object
        """
        self._redis.hset(h,k,obj)
        if self._redis.ttl(h) < 0:
            self._redis.expire(h, timeout)
        return True


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
        
        (h,k) = self._thumb_key(r, client_base, user_id, iid, size)
        return self._cache_set(h,k,obj)

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
        (h,k) = self._thumb_key(client_base, user_id, iid, size)
        r = self._redis.hget(h,k)
        if r is None:
            logger.debug('  fail: %s' % k)
        else:
            logger.debug('cached: %s' % k)
        return r

    def clearThumb (self, r, client_base, user_id, iid, size=None):
        """
        Clears thumbnail from cache. 
        
        @param r:               for cache key - Not used? 
        @param client_base:     server_id for cache key
        @param user_id:         OMERO user ID to partition caching upon
        @param iid:             image ID for cache key
        @param size:            Size used for cache key. Tuple
        @return:                True
        """
        (h,k_toss) = self._thumb_key(client_base, user_id, iid, size)
        keys = self._redis.hgetall(h)
        for k in keys:
            if self._redis.hdel(h,k) < 1:
                logger.error('failed to delete cached key %s:%s' % (h,k))
        return True


    ##
    # Image

    def _image_key (self, r, client_base, img, z=0, t=0):
        """
        Generates the hash and string key for caching the Image, based on parameters
        above, including rendering settings specified in the http request.
        
        @param r:               http request - get rendering params 'c', 'm', 'p'
        @param client_base:     server_id for cache key
        @param img:             L{omero.gateway.ImageWrapper} for ID
        @param obj:             Data to cache
        @param size:            Size used for cache key. Tuple
        """
        
        iid = img.getId()
        pre = str(iid)[:-4]
        hash_string = ''
        key_string = ''
        if len(pre) == 0:
            pre = '0'
        if r:
            r = r.REQUEST
            c = FN_REGEX.sub('-',r.get('c', ''))
            m = r.get('m', '')
            p = r.get('p', '')
            if p and not isinstance(omero.gateway.ImageWrapper.PROJECTIONS.get(p, -1),
                                    omero.constants.projection.ProjectionType): #pragma: nocover
                p = ''
            q = r.get('q', '')
            region = r.get('region', '')
            tile = r.get('tile', '')
            hash_string = 'img_%s' % client_base
            key_string = '%s/%s/%%s-c%s-m%s-q%s-r%s-t%s' % (client_base, pre, str(iid), c, m, q, region, tile)
            if p:
                return (hash_string, key_string % ('%s-%s' % (p, str(t))))
            else:
                return (hash_string, key_string % ('%sx%s' % (str(z), str(t))))
        else:
            return ('img_%s', '%s/%s' % (client_base, pre, str(iid)))

    def setImage (self, r, client_base, img, z, t, obj, ctx=''):
        """
        Puts image data into cache.
        
        @param r:               http request for cache key
        @param client_base:     server_id for cache key
        @param img:             ImageWrapper for cache key
        @param z:               Z index for cache key
        @param t:               T index for cache key
        @param obj:             Data to cache
        @param ctx:             Additional string for cache key
        """
        (h,k) = self._image_key(r, client_base, img, z, t)
        return self._cache_set(h, '%s%s' % (k, ctx),obj)

    def getImage (self, r, client_base, img, z, t, ctx=''):
        """
        Gets image data from cache. 
        
        @param r:               http request for cache key
        @param client_base:     server_id for cache key
        @param img:             ImageWrapper for cache key
        @param z:               Z index for cache key
        @param t:               T index for cache key
        @param ctx:             Additional string for cache key
        @return:                Image data
        @rtype:                 String
        """
        (h,k) = self._imageKey(r, client_base, img, z, t)
        r = self._redis.hget(h, '%s%s' % (k, ctx))
        if r is None:
            logger.debug('  fail: %s' % k)
        else:
            logger.debug('cached: %s' % k)
        return r
