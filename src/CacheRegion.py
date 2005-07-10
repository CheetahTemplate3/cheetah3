# $Id: CacheRegion.py,v 1.1 2005/07/10 18:38:39 tavis_rudd Exp $
"""Cache holder classes for Cheetah:

Cache regions are defined using the #cache Cheetah directive. Each
cache region can be viewed as a dictionnary (keyed by cacheID)
handling at least one cache (the default one). It's possible to add
caches in a region by using the `varyBy` #cache directive parameter as
in the following example::

   #cache varyBy=$getArticleID()
     #def getArticle
         this is the article content.
     #end def
   #end cache

The code above will generate a CacheRegion, and depending on the
article id value, add some new sub-caches ad-hoc.

Meta-Data
================================================================================
Author: Philippe Normand <phil@base-art.net>
Version: $Revision: 1.1 $
Start Date: 2005/06/20
Last Revision Date: $Date: 2005/07/10 18:38:39 $
"""
__author__ = "Philippe Normand <phil@base-art.net>"
__revision__ = "$Revision: 1.1 $"[11:-2]

import md5

class CacheRegion:
    """ A `CacheRegion` stores some `Cache` instances.
    """
    
    def __init__(self):
        self.clear()
        
    def clear(self):
        " drop all the caches stored in this cache region "
        self.caches = {}
        
    def getCache(self, cacheID):
        """ Lazy access to a cache

            Try to find a cache in the stored caches. If it doesn't
            exist, it's created.
            Returns a `Cache` instance.
        """
        cacheID = md5.new(str(cacheID)).hexdigest()
        if not self.caches.has_key(cacheID):
            cache = Cache(cacheID)
            self.caches[cacheID] = cache
        return self.caches.get(cacheID)
    
class Cache:
    """ Cache class.

        A Cache is a container storing:

        - cacheID (string)
        - refreshTime (timestamp or None) : last time the cache was refreshed
        - data (string) : the content of the cache

    """
    
    def __init__(self, cacheID):
        self.setID(cacheID)
        self.clear()
        
    def clear(self):
        self.setData("")
        self.setRefreshTime(None)

    def getID(self):
        return self.cacheID

    def setID(self, cacheID):
        self.cacheID = cacheID
        
    def setData(self, data):
        self.data = data

    def getData(self):
        return self.data

    def setRefreshTime(self, time):
        self.refreshTime = time

    def getRefreshTime(self):
        return self.refreshTime
