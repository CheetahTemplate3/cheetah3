#!/usr/bin/env python
# $Id: TagProcessor.py,v 1.15 2001/08/30 20:37:57 tavis_rudd Exp $
"""Tag Processor class Cheetah's codeGenerator

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.15 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/08/30 20:37:57 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.15 $"[11:-2]

##################################################
## DEPENDENCIES ##

# intra-package imports ...
from Parser import Parser

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

class TagProcessor(Parser):
    _tagType = EVAL_TAG_TYPE
    #_token is only used by the coreTagProcessors such as PlaceholderProcessor


    def __init__(self, templateObj):
        self._templateObj = templateObj
        
        ## setup some method mappings
        self.state = templateObj._state
        self.mergeNewTemplateData = templateObj.mergeNewTemplateData
        self._setTimedRefresh = templateObj._setTimedRefresh
        self.normalizePath = templateObj.normalizePath
        self.getFileContents = templateObj.getFileContents

        ## setup some attribute mappings        
        self._macros = templateObj._macros
        self._cheetahBlocks = templateObj._cheetahBlocks
        self._localVarsList = templateObj._localVarsList
        self._theFormatters = templateObj._theFormatters
        self._errorChecker = templateObj._errorChecker
        self._rawIncludes = templateObj._rawIncludes
        self._parsedIncludes = templateObj._parsedIncludes
        self._rawTextBlocks = templateObj._rawTextBlocks
        self._setVars = templateObj._setVars

        Parser.__init__(self,templateObj)


    ## Methods called automatically by the Template object   ##
    def preProcess(self, templateDef):
        delims = self.setting('internalDelims')
        tagTokenSeparator = self.setting('tagTokenSeparator')

        def subber(match, delims=delims, token=self._token,
                   tagTokenSeparator=tagTokenSeparator,
                   self=self):

            ## escape any placeholders in the tag so they aren't picked up as
            ## top-level placeholderTags
            tag = self.escapePlaceholders(match.group(1))
            
            return delims[0] + token + tagTokenSeparator  +\
                   tag + delims[1]

        for RE in self._delimRegexs:
            templateDef = RE.sub(subber, templateDef)

        return templateDef

    def templateObj(self):
        """Return a reference to the templateObj that controls this processor"""
        return self._templateObj
   
    def initializeTemplateObj(self):
        """Initialize the templateObj so that all the necessary attributes are
        in place for the tag-processing stage.  It is only called for processors
        that are registered as 'coreTagProcessors'.

        This must be called by subclasses"""

        if not self.state().has_key('basicInitDone'):
            self.state()['indentLevel'] = self.settings()['initialIndentLevel']
            self.state()['defaultCacheType'] = None
            self.state()['basicInitDone'] = True
    
    def processTag(self, tag):
        return self.wrapTagCode( self.translateTag(tag) )

    def shutdown(self):
        """This hook is called once the templateObj has been compiled, and is
        used to remove any circular references, etc."""

        self._templateObj = None        
        del self._templateObj
        for key in dir(self):
            setattr(self, key, None)
            delattr(self, key)


    ## generic methods used internally  ##
    def validateTag(self, tag):
        """A hook for doing security and syntax checks on a tag"""
        pass

    def translateTag(self, tag):
        pass

    def wrapExecTag(self, translatedTag):
        return "''')\n" + translatedTag + "write('''"

    def wrapEvalTag(self, translatedTag):
        indent = self.setting('indentationStep') * \
                 self.state()['indentLevel']
        return "''')\n" + indent + 'write(' + translatedTag + ")\n" + indent + "write('''"

    def wrapTagCode(self, translatedTag):
        if self._tagType == EVAL_TAG_TYPE:
            return self.wrapEvalTag(translatedTag)
        elif self._tagType == EXEC_TAG_TYPE:
            return self.wrapExecTag(translatedTag)
        elif self._tagType == EMPTY_TAG_TYPE:
            return ''


