#!/usr/bin/env python
# $Id: CommentDirective.py,v 1.3 2001/08/11 07:03:22 tavis_rudd Exp $
"""CommentDirective Processor class Cheetah's codeGenerator

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.3 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/08/11 07:03:22 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.3 $"[11:-2]

##################################################
## DEPENDENCIES ##

import re

# intra-package imports ...
import TagProcessor
from Parser import escCharLookBehind, escapeRegexChars, EOLZ

##################################################
## CONSTANTS & GLOBALS ##

True = (1==1)
False = (0==1)

##################################################
## CLASSES ##

class Error(Exception):
    pass

class CommentDirective(TagProcessor.TagProcessor):

    def __init__(self, templateObj):
        TagProcessor.TagProcessor.__init__(self,templateObj)
        
        single = escapeRegexChars(self.setting('singleLineComment'))       
        self.singleLineRE = re.compile(r'(?:\A|^)[\t ]*' + single + '(.*?)(?:' + EOLZ + ')|' +
                                escCharLookBehind + single + r'(.*?)$',
                                #second one doesn't gobble the \n !!!
                                re.MULTILINE)

        multiStart, multiEnd = self.setting('multiLineComment')
        self.multiStart = multiStart
        self.multiEnd = multiEnd

    def preProcess(self, templateDef):       
        templateDef = self.singleLineRE.sub('', templateDef)

        multiEnd = self.multiEnd
        multiStart = self.multiStart
        startLen = len(multiStart)
        endLen = len(multiEnd)
        
        while 1:
            s = templateDef.find(multiStart)
            if s == -1:
                break
            e = templateDef.rfind(multiEnd,s + startLen)
            if e == -1:
                e=len(templateDef)
            else:
                e += endLen
            templateDef = templateDef[:s] + templateDef[e:]
 
        return templateDef
