#!/usr/bin/env python
# $Id: CacheDirectiveProcessor.py,v 1.2 2001/08/10 19:26:02 tavis_rudd Exp $
"""CacheDirectiveProcessor & EndCacheDirectiveProcessor classes Cheetah's
codeGenerator

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.2 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/08/10 19:26:02 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.2 $"[11:-2]

##################################################
## DEPENDENCIES ##

# intra-package imports ...
import TagProcessor
from Delimiters import delimiters
import PlaceholderProcessor
##################################################
## CONSTANTS & GLOBALS ##

True = (1==1)
False = (0==1)

##################################################
## CLASSES ##

class Error(Exception):
    pass

class CacheDirectiveProcessor(TagProcessor.TagProcessor):
    _tagType = TagProcessor.EMPTY_TAG_TYPE
    _token = 'cacheDirective'
    _delimRegexs = [delimiters['cacheDirectiveStartTag'],]    

    def translateTag(self, tag):
        tag = tag.strip()
        if not tag:
            self.state()['defaultCacheType'] = \
                                       STATIC_CACHE
        else:
            self.state()['defaultCacheType'] = \
                                       TIMED_REFRESH_CACHE
            self.state()['cacheRefreshInterval'] = float(tag)

        
class EndCacheDirectiveProcessor(CacheDirectiveProcessor):
    _token = 'endCacheDirective'
    _delimRegexs = [delimiters['cacheDirectiveEndTag'],]    
    
    def translateTag(self, tag):
        self.state()['defaultCacheType'] = NoDefault
