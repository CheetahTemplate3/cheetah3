#!/usr/bin/env python
# $Id: CacheDirective.py,v 1.1 2001/08/11 01:03:16 tavis_rudd Exp $
"""CacheDirective & EndCacheDirective Processor classes Cheetah's
codeGenerator

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.1 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/08/11 01:03:16 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.1 $"[11:-2]

##################################################
## DEPENDENCIES ##
import re

# intra-package imports ...
import TagProcessor
import PlaceholderProcessor
##################################################
## CONSTANTS & GLOBALS ##

True = (1==1)
False = (0==1)

##################################################
## CLASSES ##

class Error(Exception):
    pass

class CacheDirective(TagProcessor.TagProcessor):
    _tagType = TagProcessor.EMPTY_TAG_TYPE
    _token = 'cacheDirective'

    def __init__(self, templateObj):
        TagProcessor.TagProcessor.__init__(self,templateObj)
        self._delimRegexs = self.simpleDirectiveReList(r'cache(.*?)')
        
    def translateTag(self, tag):
        tag = tag.strip()
        if not tag:
            self.state()['defaultCacheType'] = \
                                       PlaceholderProcessor.STATIC_CACHE
        else:
            self.state()['defaultCacheType'] = \
                                       PlaceholderProcessor.TIMED_REFRESH_CACHE
            self.state()['cacheRefreshInterval'] = float(tag)

        
class EndCacheDirective(CacheDirective):
    _token = 'endCacheDirective'

    def __init__(self, templateObj):
        CacheDirective.__init__(self,templateObj)
        self._delimRegexs = self.simpleDirectiveReList(r'end[\f\t ]+cache(.*?)')
        
    def translateTag(self, tag):
        self.state()['defaultCacheType'] = None
