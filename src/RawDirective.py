#!/usr/bin/env python
# $Id: RawDirective.py,v 1.4 2001/08/16 22:15:18 tavis_rudd Exp $
"""RawDirective Processor class Cheetah's codeGenerator

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.4 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/08/16 22:15:18 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.4 $"[11:-2]

##################################################
## DEPENDENCIES ##

import re

# intra-package imports ...
import TagProcessor

##################################################
## CONSTANTS & GLOBALS ##

True = (1==1)
False = (0==1)

##################################################
## CLASSES ##

class Error(Exception):
    pass

class RawDirective(TagProcessor.TagProcessor):
    """extract all chunks of the template that have been escaped with the #raw
    directive"""

    def __init__(self, templateObj):
        TagProcessor.TagProcessor.__init__(self,templateObj)
        
        bits = self._directiveREbits        
        reChunk = 'raw[\f\t ]*'
        self._startTagRegexs = self.simpleDirectiveReList(reChunk)
        self._endTagRE = re.compile(bits['start_gobbleWS'] + r'end[\f\t ]+raw[\f\t ]*' + 
                                    bits['lazyEndGrp'] + '|'+
                                    bits['start'] + r'end[\f\t ]+raw[\f\t ]*' +
                                    bits['endGrp'] + '|\Z',
                                    re.DOTALL | re.MULTILINE)
    def handleRawDirective(self, startTagMatch, templateDef):
        startToken = self.setting('directiveStartToken')
        endToken = self.setting('directiveEndToken')
        
        endTagMatch = self._endTagRE.search(templateDef)           
        unparsedBlock = templateDef[startTagMatch.end() : endTagMatch.start()]

        blockID = '_' + str(id(unparsedBlock))
        self._rawTextBlocks[blockID] = unparsedBlock
        
        replacementStr =  startToken + 'include raw ' + \
                         self.setting('placeholderStartToken') \
                         + 'rawTextBlocks.' + blockID + endToken
        
        return templateDef[0:startTagMatch.start()] + replacementStr + \
               templateDef[endTagMatch.end():]
        
    def preProcess(self, templateDef):
        for startTagRE in self._startTagRegexs:
            while startTagRE.search(templateDef):
                startTagMatch = startTagRE.search(templateDef)
                templateDef = self.handleRawDirective(startTagMatch=startTagMatch,
                                                  templateDef=templateDef)
        return templateDef
