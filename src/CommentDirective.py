#!/usr/bin/env python
# $Id: CommentDirective.py,v 1.1 2001/08/11 02:29:33 tavis_rudd Exp $
"""CommentDirective Processor class Cheetah's codeGenerator

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.1 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/08/11 02:29:33 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.1 $"[11:-2]

##################################################
## DEPENDENCIES ##

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

class CommentDirective(TagProcessor.TagProcessor):

    def __init__(self, templateObj):
        TagProcessor.TagProcessor.__init__(self,templateObj)
        import re
        from Parser import escCharLookBehind
        singleLine = re.compile(r'(?:\A|^)[\t ]*##(.*?)(?:\r\n|\n|\r|\Z)|' +
                                escCharLookBehind + r'##(.*?)$', #this one doesn't gobble the \n !!!
                                re.MULTILINE),

        multiLine =  re.compile(escCharLookBehind + r'#\*' +
                                r'(.*?)' +
                                r'(?:\*#|\Z)',
                                re.DOTALL | re.MULTILINE),

        self._delimRegexs = [singleLine, multiLine]
        
    def preProcess(self, templateObj, templateDef):
        def subber(match):
            return ''
        
        for regex in self._delimRegexs:
            templateDef = regex.sub(subber, templateDef)
        return templateDef
