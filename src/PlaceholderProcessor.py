#!/usr/bin/env python
# $Id: PlaceholderProcessor.py,v 1.26 2001/08/13 01:58:28 tavis_rudd Exp $
"""Provides utilities for processing $placeholders in Cheetah templates

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>,
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.26 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2001/08/13 01:58:28 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.26 $"[11:-2]


##################################################
## DEPENDENCIES ##

import re
from random import randrange

#intra-package dependencies ...
from TagProcessor import TagProcessor
import NameMapper
from NameMapper import valueForName

##################################################
## GLOBALS AND CONSTANTS ##

True = (1==1)
False = (1==0)

# cacheType's for $placeholders
NO_CACHE = 0
STATIC_CACHE = 1
TIMED_REFRESH_CACHE = 2

##################################################
## CLASSES ##

class PlaceholderProcessor(TagProcessor):
    """A class for processing $placeholders in strings."""
    
    _token = 'placeholders'

    ## methods called by the Template Object
    
    def preProcess(self, templateDef):
        """Wrap all marked placeholders in a string with Cheetah's internal delims."""
        templateDef = self.wrapExressionsInStr(self.markPlaceholders(templateDef),
                                               marker=self.setting('placeholderMarker'),
                                               before=self.setting('internalDelims')[0] + \
                                               self._token + self.setting('tagTokenSeparator'),
                                               after=self.setting('internalDelims')[1])
        
        return self.unescapePlaceholders(templateDef)
        
    def processTag(self, tag):

        """This method is called by the Template class for every $placeholder
        tag in the template definition

        It is a wrapper around self.translatePlaceholderString that deals with caching"""

        templateObj = self.templateObj()
        state = self.state()
        
        ## find out what cacheType the tag has
        if not state['defaultCacheType'] == None:
            cacheType = state['defaultCacheType']
            if cacheType == TIMED_REFRESH_CACHE:
                cacheRefreshInterval = \
                        state['cacheRefreshInterval']
        else:
            cacheType = NO_CACHE

        ## examine the namechunks for the caching keywords
        nameChunks = tag.split('.')
        if nameChunks[0] == 'CACHED':
            del nameChunks[0]
            cacheType = STATIC_CACHE
        if nameChunks[0].startswith('REFRESH'):
            cacheType = TIMED_REFRESH_CACHE
            cacheRefreshInterval = float('.'.join(nameChunks[0].split('_')[1:]))
            del nameChunks[0]
        tag = '.'.join(nameChunks)


        ## translate the tag into Python code using self.translatePlaceholderString
        translatedTag = self.translatePlaceholderString(
            self.setting('placeholderMarker') + tag)

        
        ## deal with caching 
        currFormatter = state['currFormatter']
        formatterTag = 'theFormatters["' + currFormatter + '"](' \
                        + translatedTag + ')'
        if cacheType == STATIC_CACHE:
            return self.evalPlaceholderString(formatterTag)
        elif cacheType == TIMED_REFRESH_CACHE:
            ID = str(id(translatedTag)) + '_' + str(randrange(1000, 9000))
            templateObj._setTimedRefresh(ID, formatterTag, cacheRefreshInterval)
            translatedTag = 'timedRefreshCache["' + ID + '"]'

        ## return the proper code to the code-generator
        if self.state()['interactiveFormatter']:
            return self.wrapEvalTag("format(" + translatedTag + ", trans=trans)")
        else:
            return self.wrapEvalTag("format(" + translatedTag + ")")

            


