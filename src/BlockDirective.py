#!/usr/bin/env python
# $Id: BlockDirective.py,v 1.2 2001/08/11 04:57:39 tavis_rudd Exp $
"""BlockDirective Processor class Cheetah's codeGenerator

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.2 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/08/11 04:57:39 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.2 $"[11:-2]

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
        
        templateObj = self.templateObj()
        startToken = templateObj.setting('directiveStartToken')
        endToken = templateObj.setting('directiveEndToken')

        def handleBlock(blockName, startTagMatch, endTagRE,
                        templateDef=templateDef, templateObj=templateObj,
                        startToken=startToken, endToken=endToken):
    
            endTagMatch = endTagRE.search(templateDef)
            blockContents = templateDef[startTagMatch.end() : endTagMatch.start()]
    
            if not templateObj._cheetahBlocks.has_key(blockName):
                templateObj._cheetahBlocks[blockName] = blockContents
    
            if templateObj.setting('includeBlockMarkers'):
                markerStart = templateObj._settings['blockMarkerStart']
                markerEnd = templateObj._settings['blockMarkerEnd']
            
                replaceString = markerStart[0] + blockName + markerStart[1] + \
                       startToken + 'include direct ' + templateObj.setting('placeholderStartToken') + \
                       'cheetahBlocks.' + blockName + endToken + \
                       markerEnd[0] + blockName + markerEnd[1]
            else:
                replaceString = startToken + 'include direct ' + \
                                templateObj.setting('placeholderStartToken') + \
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
