#!/usr/bin/env python
# $Id: CacheDirectiveProcessor.py,v 1.1 2001/08/02 06:00:38 tavis_rudd Exp $
"""CacheDirectiveProcessor & EndCacheDirectiveProcessor classes Cheetah's
codeGenerator

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.1 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/08/02 06:00:38 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.1 $"[11:-2]

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

    def translateTag(self, templateObj, tag):
        tag = tag.strip()
        if not tag:
            templateObj._codeGeneratorState['defaultCacheType'] = \
                                     PlaceholderProcessor.STATIC_CACHE
        else:
            templateObj._codeGeneratorState['defaultCacheType'] = \
                                     PlaceholderProcessor.TIMED_REFRESH_CACHE
            templateObj._codeGeneratorState['cacheRefreshInterval'] = float(tag)

        
class EndCacheDirectiveProcessor(CacheDirectiveProcessor):
    _token = 'endCacheDirective'
    _delimRegexs = [delimiters['cacheDirectiveEndTag'],]    
    
    def translateTag(self, templateObj, tag):
        templateObj._codeGeneratorState['defaultCacheType'] = None
