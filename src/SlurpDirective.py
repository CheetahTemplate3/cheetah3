#!/usr/bin/env python
# $Id: SlurpDirective.py,v 1.2 2001/08/11 04:57:39 tavis_rudd Exp $
"""SlurpDirective Processor class Cheetah's codeGenerator

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

class SlurpDirective(TagProcessor.TagProcessor):

    def __init__(self, templateObj):
        TagProcessor.TagProcessor.__init__(self,templateObj)
        self._delimRegexs = self.simpleDirectiveReList(r'slurp[\f\t ]*')
        
    def preProcess(self, templateDef):
        def subber(match):
            return ''
        
        for regex in self._delimRegexs:
            templateDef = regex.sub(subber, templateDef)
        return templateDef
