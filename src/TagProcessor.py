#!/usr/bin/env python
# $Id: TagProcessor.py,v 1.2 2001/08/03 19:20:50 tavis_rudd Exp $
"""Tag Processor class Cheetah's codeGenerator

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.2 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/08/03 19:20:50 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.2 $"[11:-2]

##################################################
## DEPENDENCIES ##

import re

# intra-package imports ...

##################################################
## CONSTANTS & GLOBALS ##

True = (1==1)
False = (0==1)

# tag types for the main tags
EVAL_TAG_TYPE = 0
EXEC_TAG_TYPE = 1
EMPTY_TAG_TYPE = 2

##################################################
## CLASSES ##

class Error(Exception):
    pass

class TagProcessor:
    _tagType = EVAL_TAG_TYPE

    def __init__(self):
        pass

    def preProcess(self, templateObj, templateDef):
        delims = templateObj.setting('internalDelims')
        tagTokenSeparator = templateObj.setting('tagTokenSeparator')
        def subber(match, delims=delims, token=self._token,
                   tagTokenSeparator=tagTokenSeparator,
                   templateObj=templateObj):

            ## escape any placeholders in the tag so they aren't picked up as
            ## top-level placeholderTags
            tag = templateObj.placeholderProcessor.escapePlaceholders(match.group(1))
            
            return delims[0] + token + tagTokenSeparator  +\
                   tag + delims[1]

        for RE in self._delimRegexs:
            templateDef = RE.sub(subber, templateDef)

        return templateDef
   
    def initializeTemplateObj(self, templateObj):
        """Initialize the templateObj so that all the necessary attributes are
        in place for the tag-processing stage

        This must be called by subclasses"""
        
        if not templateObj._codeGeneratorState.has_key('indentLevel'):
            templateObj._codeGeneratorState['indentLevel'] = \
                          templateObj._settings['initialIndentLevel']
        if not hasattr(templateObj, '_localVarsList'):
            # may have already been set by #set or #for
            templateObj._localVarsList = []
            
        if not hasattr(templateObj,'_perResponseSetupCodeChunks'):
            templateObj._perResponseSetupCodeChunks = {}

        if not templateObj._codeGeneratorState.has_key('defaultCacheType'):
            templateObj._codeGeneratorState['defaultCacheType'] = None

    
    def processTag(self, templateObj, tag):
        return self.wrapTagCode( templateObj, self.translateTag(templateObj, tag) )

    def translateTag(self, templateObj, tag):
        pass

    def wrapExecTag(self, templateObj, translatedTag):
        return "''',])\n" + translatedTag + "outputList.extend(['''"

    def wrapEvalTag(self, templateObj, translatedTag):
        indent = templateObj._settings['indentationStep'] * \
                 templateObj._codeGeneratorState['indentLevel']
        return "''',\n" + indent + translatedTag + ", '''"

    def wrapTagCode(self, templateObj, translatedTag):
        if self._tagType == EVAL_TAG_TYPE:
            return self.wrapEvalTag(templateObj, translatedTag)
        elif self._tagType == EXEC_TAG_TYPE:
            return self.wrapExecTag(templateObj, translatedTag)
        elif self._tagType == EMPTY_TAG_TYPE:
            return ''
