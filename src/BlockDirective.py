#!/usr/bin/env python
# $Id: BlockDirective.py,v 1.5 2001/08/16 22:15:17 tavis_rudd Exp $
"""BlockDirective Processor class Cheetah's codeGenerator

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.5 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/08/16 22:15:17 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.5 $"[11:-2]

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

class BlockDirective(TagProcessor.TagProcessor):

    def __init__(self, templateObj):
        TagProcessor.TagProcessor.__init__(self,templateObj)
        reChunk = 'block[\f\t ]+(?P<blockName>[A-Za-z_][A-Za-z_0-9]*?)[\f\t ]*'
        self._startTagRegexs = self.simpleDirectiveReList(reChunk)
        
        bits = self._directiveREbits
        self._endTagTemplate = bits['start_gobbleWS'] + r'end[\f\t ]+block[\f\t ]+' + \
                               '%(blockName)s' + \
                               r'[\f\t ]*' + bits['lazyEndGrp'] + '|'+ \
                               bits['start'] + r'end[\f\t ]+block[\f\t ]+' + \
                               '%(blockName)s' + \
                               r'[\f\t ]*' + bits['endGrp']
        

    def handleBlock(self, blockName, startTagMatch, endTagRE, templateDef):
        
        endTagMatch = endTagRE.search(templateDef)
        if not endTagMatch:
            raise Error("Cheetah couldn't find the end tag for the #block titled '" +
                        blockName + "'.")
        
        blockContents = templateDef[startTagMatch.end() : endTagMatch.start()]

        if not self._cheetahBlocks.has_key(blockName):
            self._cheetahBlocks[blockName] = blockContents

        startToken = self.setting('directiveStartToken')
        endToken = self.setting('directiveEndToken')

        if self.setting('includeBlockMarkers'):
            markerStart = self.setting('blockMarkerStart')
            markerEnd = self.setting('blockMarkerEnd')
        
            replaceString = markerStart[0] + blockName + markerStart[1] + \
                   startToken + 'include direct ' + self.setting('placeholderStartToken') + \
                   'cheetahBlocks.' + blockName + endToken + \
                   markerEnd[0] + blockName + markerEnd[1]
        else:
            replaceString = startToken + 'include direct ' + \
                            self.setting('placeholderStartToken') + \
                            'cheetahBlocks.' + blockName + endToken

        return templateDef[0:startTagMatch.start()] + replaceString + \
                   templateDef[endTagMatch.end():]

    def preProcess(self, templateDef):
        for startTagRE in self._startTagRegexs:
            while startTagRE.search(templateDef):
                startTagMatch = startTagRE.search(templateDef)
                blockName = startTagMatch.group('blockName')
                endTagRE = re.compile((self._endTagTemplate % {'blockName':blockName}),
                                      re.DOTALL | re.MULTILINE)
                templateDef = self.handleBlock(blockName, startTagMatch, endTagRE,
                                               templateDef=templateDef)
        
        return templateDef
