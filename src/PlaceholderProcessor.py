#!/usr/bin/env python
# $Id: PlaceholderProcessor.py,v 1.22 2001/08/10 22:44:36 tavis_rudd Exp $
"""Provides utilities for processing $placeholders in Cheetah templates

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>,
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.22 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2001/08/10 22:44:36 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.22 $"[11:-2]


##################################################
## DEPENDENCIES ##

import re

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

    def wrapPlaceholders(self, txt):
        """Wrap all marked placeholders in a string with Cheetah's internal delims."""
        return self.wrapExressionsInStr(txt, marker=self.setting('placeholderMarker'),
                                        before=self.setting('internalDelims')[0] + \
                                        self._token + self.setting('tagTokenSeparator'),
                                        after=self.setting('internalDelims')[1])


    ## methods called by the Template Object
    
    def preProcess(self, templateObj, templateDef):
        """Do the preProcessing stuff for stage 1 of the Template class'
        code-generator"""
        return self.wrapPlaceholders(self.markPlaceholders(templateDef))

    
    def initializeTemplateObj(self):
        """Initialize the templateObj so that all the necessary attributes are
        in place for the tag-processing stage"""

        templateObj = self.templateObj()
        TagProcessor.initializeTemplateObj(self)
        
        if not templateObj._perResponseSetupCodeChunks.has_key('placeholders'):
            ## setup the code to be included at the beginning of each response ##
            indent = templateObj._settings['indentationStep']
            baseInd = indent  * \
                   templateObj._settings['initialIndentLevel']

            templateObj._perResponseSetupCodeChunks['placeholders'] = \
                      baseInd + "if self._checkForCacheRefreshes:\n"\
                      + baseInd + indent + "timedRefreshCache = self._timedRefreshCache\n" \
                      + baseInd + indent + "currTime = currentTime()\n"\
                      + baseInd + indent + "self._timedRefreshList.sort()\n"\
                      + baseInd + indent + "if currTime >= self._timedRefreshList[0][0]:\n"\
                      + baseInd + indent * 2 +  " self._timedRefresh(currTime)\n"\
                      + baseInd + indent + "                                   \n" \
                      + baseInd + "nestedTemplates = self._nestedTemplatesCache\n" \
                      + baseInd + "components = self._componentsDict\n"

            ## initialize the caches, the localVarsList, and the timedRefreshList
            templateObj._timedRefreshCache = {} # caching timedRefresh vars
            templateObj._nestedTemplatesCache = {} # caching references to nested templates
            templateObj._componentsDict = {}       # you get the idea...
            templateObj._timedRefreshList = []
            templateObj._checkForCacheRefreshes = False
        
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

        
        ## deal with the caching and return the proper code to the code-generator
        searchList = templateObj.searchList()
        if cacheType == STATIC_CACHE:
            searchList_getMeth = searchList.get # shortcut-namebing in the eval
            return str(
                self.evalPlaceholderString(translatedTag)).replace("'''",r"\'\'\'")
        elif cacheType == TIMED_REFRESH_CACHE:
            templateObj._setTimedRefresh(translatedTag, cacheRefreshInterval)
            return self.wrapEvalTag(
                'timedRefreshCache["""' + translatedTag + '"""]')
        else:
            return self.wrapEvalTag("str(" + translatedTag + ")")

            


