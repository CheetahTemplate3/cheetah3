#!/usr/bin/env python
# $Id: StopDirective.py,v 1.4 2001/09/15 23:57:48 tavis_rudd Exp $
"""StopDirective Processor class Cheetah's codeGenerator

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.4 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/09/15 23:57:48 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.4 $"[11:-2]

##################################################
## DEPENDENCIES ##

# intra-package imports ...
import TagProcessor

##################################################
## CLASSES ##

class StopDirective(TagProcessor.TagProcessor):
    _tagType = TagProcessor.EXEC_TAG_TYPE
    _token = 'stopDirective'

    def __init__(self, templateObj):
        TagProcessor.TagProcessor.__init__(self,templateObj)
        self._delimRegexs = self.simpleDirectiveReList(r'stop(.*?)')

    def translateTag(self, tag):
        indent = self.setting('indentationStep')
        
        outputCode = """%(baseInd)sif dummyTrans:
%(baseInd)s    return trans.response().getvalue()
%(baseInd)selse: return ''
%(baseInd)s""" % {'baseInd':indent*self.state()['indentLevel']}
        
        return outputCode
