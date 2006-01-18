# $Id: CacheRegion.py,v 1.2 2006/01/18 03:17:58 tavis_rudd Exp $
"""Cache holder classes for Cheetah:

Cache regions are defined using the #cache Cheetah directive. Each
cache region can be viewed as a dictionnary (keyed by cacheID)
handling at least one cache (the default one). It's possible to add
caches in a region by using the `varyBy` #cache directive parameter as
in the following example::
   #def getArticle
      this is the article content.
   #end def

   #cache varyBy=$getArticleID()
      $getArticle($getArticleID())
   #end cache

The code above will generate a CacheRegion, and depending on the
article id value, add some new sub-caches ad-hoc.

Meta-Data
================================================================================
Author: Philippe Normand <phil@base-art.net>
Version: $Revision: 1.2 $
Start Date: 2005/06/20
Last Revision Date: $Date: 2006/01/18 03:17:58 $
"""
__author__ = "Philippe Normand <phil@base-art.net>"
__revision__ = "$Revision: 1.2 $"[11:-2]

import md5
    
class Cache:
    """ Cache class.

    A Cache is a container storing:

        - cacheID (string)
        - refreshTime (timestamp or None) : last time the cache was refreshed
        - data (string) : the content of the cache

    This implementation stores the data in the memory of the current process.
    If you need a more advanced data store, consider subclassing this and making
    it a wrapper around the Python memcached API
    (http://www.danga.com/memcached).   
    """
    
    def __init__(self, regionID, cacheID):
        self._regionID = regionID
        self._cacheID = cacheID
        self._data = None
        self._refreshTime = None

    def clear(self):
        self._data = ""
        self._refreshTime = None

    def getID(self):
        return self._cacheID

    def setID(self, cacheID):
        self._cacheID = cacheID

    def setData(self, data):
        self._data = data

    def getData(self):
        return self._data

    def hasData(self):
        return self._data is not None

    def getOutput(self):
        """Can be overridden to implement edge-caching"""
        return self._data or ""

    def setRefreshTime(self, time):
        self._refreshTime = time

    def getRefreshTime(self):
        return self._refreshTime


class CacheRegion:
    """ A `CacheRegion` stores some `Cache` instances.
    """
    _cacheClass = Cache
    
    def __init__(self, regionID):
        self._regionID = regionID
        self._cacheItems = {}
        self._isNew = True
        
    def isNew(self):
        return self._isNew
        
    def clear(self):
        " drop all the caches stored in this cache region "
        self._cacheItems.clear()
        
    def getCacheItem(self, cacheID):
        """ Lazy access to a cache

            Try to find a cache in the stored caches. If it doesn't
            exist, it's created.
            Returns a `Cache` instance.
        """
        cacheID = md5.new(str(cacheID)).hexdigest()
        if not self._cacheItems.has_key(cacheID):
            cache = self._cacheClass(regionID=self._regionID, cacheID=cacheID)
            self._cacheItems[cacheID] = cache
            self._isNew = False
        return self._cacheItems[cacheID]
