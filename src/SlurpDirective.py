#!/usr/bin/env python
# $Id: SlurpDirective.py,v 1.4 2001/09/15 23:53:55 tavis_rudd Exp $
"""SlurpDirective Processor class Cheetah's codeGenerator

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.4 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/09/15 23:53:55 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.4 $"[11:-2]

##################################################
## DEPENDENCIES ##

# intra-package imports ...
import TagProcessor

##################################################
## CLASSES ##

class SlurpDirective(TagProcessor.TagProcessor):

    def __init__(self, templateObj):
        TagProcessor.TagProcessor.__init__(self,templateObj)
        self._delimRegexs = self.simpleDirectiveReList(r'slurp[\f\t ]*')
        
    def preProcess(self, templateDef):       
        for regex in self._delimRegexs:
            templateDef = regex.sub('', templateDef)
        return templateDef
