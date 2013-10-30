#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Webgateway cache using redis
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
import traceback

logger = logging.getLogger(__name__)

CACHE_ENABLED = None
try:
    import redis
    CACHE_ENABLED = True
except:
    logger.warning('Redis Python module not found. Disabling caching.')
    CACHE_ENABLED  = False
import re

FN_REGEX = re.compile('[#$,|]')

class WebGatewayCacheNull(object):
    """
    Base object for when no caching is enabled.
    """
    def __init__(self):
        pass

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

    def clear(self):
        pass

    def invalidateObject (self, client_base, user_id, obj):
        pass

    def setThumb(self, r, client_base, user_id, iid, obj, size=()):
        return None

    def getThumb(self, r, client_base, user_id, iid, size=()):
        return None

    def clearThumb(self, r, client_base, user_id, iid, size=None):
        return True

    def setImage(self, r, client_base, img, z, t, obj, ctx=''):
        return None

    def getImage(self, r, client_base, img, z, t, ctx=''):
        return None

    def clearImage(self, r, client_base, user_id, img, skipJson=False):
        return None

    def setSplitChannelImage(self, r, client_base, img, z, t, obj):
        """ Calls L{setImage} with '-sc' context """
        return self.setImage(r, client_base, img, z, t, obj, '-sc')

    def getSplitChannelImage(self, r, client_base, img, z, t):
        """
        Calls L{getImage} with '-sc' context
        @rtype:     String
        """
        return self.getImage(r, client_base, img, z, t, '-sc')

    def setOmeTiffImage(self, r, client_base, img, obj):
        """ Calls L{setImage} with '-ometiff' context """
        return self.setImage(r, client_base, img, 0, 0, obj, '-ometiff')

    def getOmeTiffImage(self, r, client_base, img):
        """
        Calls L{getImage} with '-ometiff' context
        @rtype:     String
        """
        return self.getImage(r, client_base, img, 0, 0, '-ometiff')

    def setJson(self, r, client_base, obj, data, ctx=''):
        return None

    def getJson(self, r, client_base, obj, ctx=''):
        return None

    def clearJson(self, client_base, obj, ctx=''):
        return True

    def setDatasetContents(self, r, client_base, ds, data):
        """
        Adds data to the json cache using 'contents' as context

        @param r:               http request - not used
        @param client_base:     server_id for cache key
        @param ds:              ObjectWrapper for cache key
        @param data:            Data to cache
        @rtype:                 True
        """
        return self.setJson(r, client_base, ds, data, 'contents')

    def getDatasetContents(self, r, client_base, ds):
        """
        Gets data from the json cache using 'contents' as context

        @param r:               http request - not used
        @param client_base:     server_id for cache key
        @param ds:              ObjectWrapper for cache key
        @rtype:                 String or None
        """
        return self.getJson(r, client_base, ds, 'contents')


class WebGatewayCacheRedis(WebGatewayCacheNull):
    """
    Experiemental rewrite of WebGatewayeCache using Redis as the caching
    backend.
    """

    def __init__(self):
        self._redis_host = getattr(settings, 'REDIS_HOST', 'localhost')
        self._redis_port = getattr(settings, 'REDIS_PORT', 6379)
        self._redis_db = getattr(settings, 'REDIS_DB', 0)
        self._default_timeouts = getattr(settings, 'REDIS_DEFAULT_TIMEOUTS', None)
        self._connected = False
        self._connect_to_redis()

    def _connect_to_redis(self):
        """
        Wraps our redis connection in a reproducable way
        """
        if not self._connected:
            try:
                self._redis = redis.StrictRedis(host=self._redis_host, \
                    port=self._redis_port, db=self._redis_db)
                self._connected = True
            except:
                self._connected = False
                logger.warning('Unable to connect to Redis DB for caching')
                for w in traceback.format_exc().splitlines():
                    logger.debug(w)

    def clear (self):
        """
        Attempts to clear all the values stored in redis as hash/key/cahce.
        """
        if self._connected:
            try:
                self._redis.flushall()
            except:
                logger.warning("Problem trying to clear the Redis cache")
                for w in traceback.format_exc().splitlines():
                    logger.debug(w)

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

    def _get_timeout(self, key):
        """
        Obtains the timeout for a given cache. If no cache is found for key,
        will default to 'None'.

        @oaram key:             The cache key to look for.
        @return:                The timeout found, or 'None'.
        """
        if self._default_timeouts.has_key(key):
            return self._default_timeouts[key]
        return None

    def _cache_set(self, h, k, obj, timeout):
        """
        Sets the cache.

        @param h:               The hash_key for the cache
        @param k:               The key for the cache
        @param obj:             The object to cache
        @param timeout:         The timeout for the object
        """
        if self._connected:
            try:
                self._redis.hset(h,k,obj)
                if timeout is not None:
                    self._redis.expire(h, timeout)
            except:
                logger.warning("Problem trying to cache a key with Redis")
                for w in traceback.format_exc().splitlines():
                    logger.debug(w)


        return True

    def _cache_del(self, h, k):
        """
        Delete an element from the cache given hash_string and key
        """
        try:
            if self._redis.hdel(h,k) < 1:
                logger.error('failed to delete cached key %s:%s' % (h,k))
        except:
            logger.warning("Problem deleting a key from Redis")
            for w in traceback.format_exc().splitlines():
                    logger.debug(w)

    def _cache_get(self, h, k):
        """
        Obtains the object based upon hash_string and key
        """
        r = None
        try:
            r = self._redis.hget(h,k)
        except:
            logger.warning('Problem getting a key from Redis')
            for w in traceback.format_exc().splitlines():
                    logger.debug(w)

        if r is None:
            logger.debug('  fail: %s' % k)
        else:
            logger.debug('cached: %s' % k)
        return r


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
        hash_string = 'thumb_user_%s' % client_base
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

        (h,k) = self._thumb_key(client_base, user_id, iid, size)

        return self._cache_set(h,k,obj, self._get_timeout('thumbnail'))

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
        return self._cache_get(h,k)

    def clearThumb(self, r, client_base, user_id, iid, size=None):
        """
        Clears thumbnail from cache.

        @param r:               for cache key - Not used?
        @param client_base:     server_id for cache key
        @param user_id:         OMERO user ID to partition caching upon
        @param iid:             image ID for cache key
        @param size:            Size used for cache key. Tuple
        @return:                True
        """
        if self._connected:
            try:
                (h,k_toss) = self._thumb_key(client_base, user_id, iid, size)
                keys = self._redis.hgetall(h)
                for k in keys:
                    self._cache_del(h,k)
            except:
                logger.warning('Could not clear thumbnails from cache')
                for w in traceback.format_exc().splitlines():
                    logger.debug(w)
        return True


    ##
    # Image

    def _image_key(self, r, client_base, img, z=0, t=0):
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
            key_string = '%s/%s/%%s-c%s-m%s-q%s-r%s-t%s' % (pre, str(iid), c, m, q, region, tile)
            if p:
                return (hash_string, key_string % ('%s-%s' % (p, str(t))))
            else:
                return (hash_string, key_string % ('%sx%s' % (str(z), str(t))))
        else:
            return ('img_%s' % client_base, '%s/%s' % (pre, str(iid)))

    def setImage(self, r, client_base, img, z, t, obj, ctx=''):
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
        return self._cache_set(h, '%s%s' % (k, ctx),obj,self._get_timeout('image'))

    def getImage(self, r, client_base, img, z, t, ctx=''):
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
        (h,k) = self._image_key(r, client_base, img, z, t)
        return self._cache_get(h, '%s%s' % (k, ctx))

    def clearImage(self, r, client_base, user_id, img, skipJson=False):
        """
        Clears image data from cache using default rendering settings (r=None) T and Z indexes ( = 0).
        TODO: Doesn't clear any data stored WITH r, t, or z specified in cache key?
        Also clears thumbnail (but not thumbs with size specified) and json data for this image.

        @param r:               http request for cache key
        @param client_base:     server_id for cache key
        @param user_id:         OMERO user ID to partition caching upon
        @param img:             ImageWrapper for cache key
        @param obj:             Data to cache
        @param rtype:           True
        """
        if self._connected:
            (h,k_toss) = self._image_key(None, client_base, img)
            try:
                keys = self._redis.hgetall(h)
                for k in keys:
                    self._cache_del(h,k)
            except:
                logger.warning('Could not clear image cache')
                for w in traceback.format_exc().splitlines():
                    logger.debug(w)
            # do the thumb too
            self.clearThumb(r, client_base, user_id, img.getId())
            # and json data
            if not skipJson:
                self.clearJson(client_base, img)
        return True


    ##
    # hierarchies (json)

    def _json_key(self, r, client_base, obj, ctx=''):
        """
        Generates the hash and string key for storing json data based on
        params above.

        @param r:               http request - not used
        @param client_base:     server_id
        @param obj:             ObjectWrapper
        @param ctx:             Additional string for cache key
        @return:                Cache key
        @rtype:                 String
        """

        if obj:
            return ('json_%s' % client_base, '%s_%s/%s' % (obj.OMERO_CLASS, obj.id, ctx))
        else:
            return ('json_%s' % client_base, 'single/%s' % (client_base, ctx))

    def setJson(self, r, client_base, obj, data, ctx=''):
        """
        Adds data to the json cache

        @param r:               http request - not used
        @param client_base:     server_id for cache key
        @param obj:             ObjectWrapper for cache key
        @param data:            Data to cache
        @param ctx:             context string used for cache key
        @rtype:                 True
        """
        (h,k) = self._json_key(r, client_base, obj, ctx)
        return self._cache_set(h, k, data, self._get_timeout('json'))

    def getJson(self, r, client_base, obj, ctx=''):
        """
        Gets data from the json cache

        @param r:               http request - not used
        @param client_base:     server_id for cache key
        @param obj:             ObjectWrapper for cache key
        @param ctx:             context string used for cache key
        @rtype:                 String or None
        """
        (h,k) = self._json_key(r, client_base, obj, ctx)
        return self._cache_get(h,k)

    def clearJson(self, client_base, obj, ctx=''):
        """
        Clears image data from cache using default rendering settings (r=None) T and Z indexes ( = 0).

        @param client_base:     server_id for cache key
        @param obj:             Data to cache
        @param ctx:             context string used for cache key
        @return:           True
        WAS: Only handles Dataset obj, calling L{clearDatasetContents}
        """
        if self._connected:
            (h,k_toss) = self._json_key(None, client_base, obj, ctx)
            try:
                keys = self._redis.hgetall(h)
                for k in keys:
                    self._cache_del(h,k)
            except:
                logger.warning('Could not clear JSON cache')
                for w in traceback.format_exc().splitlines():
                    logger.debug(w)
        return True

    def clearDatasetContents(self, r, client_base, ds):
        """
        Clears data from the json cache using 'contents' as context

        @param r:               http request - not used
        @param client_base:     server_id for cache key
        @param ds:              ObjectWrapper for cache key
        @rtype:                 True
        """
        if self._connected:
            (h,k_toss) = self._json_key(r, client_base, ds, 'contents')
            try:
                keys = self._redis.hgetall(h)
                for k in keys:
                    self._cache_del(h,k)
            except:
                logger.warning('Unable to clear json cache using contents as context')
                for w in traceback.format_exc().splitlines():
                    logger.debug(w)
        return True

if CACHE_ENABLED:
    webgateway_cache = WebGatewayCacheRedis()
else:
    webgateway_cache = WebGatewayCacheNull()
