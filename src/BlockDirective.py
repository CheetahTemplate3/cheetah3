#!/usr/bin/env python
# $Id: BlockDirective.py,v 1.4 2001/08/16 05:01:37 tavis_rudd Exp $
"""BlockDirective Processor class Cheetah's codeGenerator

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.4 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/08/16 05:01:37 $
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

class BlockDirective(TagProcessor.TagProcessor):

    def __init__(self, templateObj):
        TagProcessor.TagProcessor.__init__(self,templateObj)
        reChunk = 'block[\t ]+(?P<blockName>[A-Za-z_][A-Za-z_0-9]*?)[\f\t ]*'
        self._delimRegexs = self.simpleDirectiveReList(reChunk)
        
    def preProcess(self, templateDef):
        
        startToken = self.setting('directiveStartToken')
        endToken = self.setting('directiveEndToken')

        def handleBlock(blockName, startTagMatch, endTagRE,
                        templateDef=templateDef, self=self,
                        startToken=startToken, endToken=endToken):
    
            endTagMatch = endTagRE.search(templateDef)
            blockContents = templateDef[startTagMatch.end() : endTagMatch.start()]
    
            if not self._cheetahBlocks.has_key(blockName):
                self._cheetahBlocks[blockName] = blockContents
    
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

   
        ## 
        bits = self._directiveREbits
        
        for startTagRE in self._delimRegexs:
            while startTagRE.search(templateDef):
                startTagMatch = startTagRE.search(templateDef)
                blockName = startTagMatch.group('blockName')
                endTagRE = re.compile(bits['start_gobbleWS'] + r'end block[\t ]+' + \
                                      blockName +
                                      r'[\t ]*' + bits['lazyEndGrp'] + '|'+
                                      startToken + r'end block[\t ]+' + blockName +
                                      r'[\t ]*' + bits['endGrp'],
                                      re.DOTALL | re.MULTILINE)
                templateDef = handleBlock(blockName, startTagMatch, endTagRE,
                                       templateDef=templateDef)
        
        return templateDef
