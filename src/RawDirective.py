#!/usr/bin/env python
# $Id: RawDirective.py,v 1.3 2001/08/15 17:49:51 tavis_rudd Exp $
"""RawDirective Processor class Cheetah's codeGenerator

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.3 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/08/15 17:49:51 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.3 $"[11:-2]

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
        
        RE = re.compile(r'#raw[\t ]*(?:/#|\r\n|\n|\r|\Z)(.*?)' +
                   r'(?:(?:#end raw[\t ]*(?:/#|\r\n|\n|\r))|\Z)',
                   re.DOTALL)
        self._delimRegexs = [RE,] #self.simpleDirectiveReList(r'slurp[\f\t ]*')
        
    def preProcess(self, templateDef):
        startToken = self.setting('directiveStartToken')
        endToken = self.setting('directiveEndToken')
        
        def subber(match, self=self, startToken=startToken,
                   endToken=endToken):
            unparsedBlock = match.group(1)
            blockID = '_' + str(id(unparsedBlock))
            self._rawTextBlocks[blockID] = unparsedBlock
            
            return startToken + 'include raw ' + \
                   self.setting('placeholderStartToken') \
                   + 'rawTextBlocks.' + blockID + endToken
                    
        for regex in self._delimRegexs:
            templateDef = regex.sub(subber, templateDef)
        return templateDef
        
