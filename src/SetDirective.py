#!/usr/bin/env python
# $Id: SetDirective.py,v 1.2 2001/08/13 01:58:28 tavis_rudd Exp $
"""SetDirective Processor class Cheetah's codeGenerator

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.2 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/08/13 01:58:28 $
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

class SetDirective(TagProcessor.TagProcessor):
    """A class for processing display logic tags in Cheetah Templates."""
    
    _token = 'setDirective'
    _tagType = TagProcessor.EXEC_TAG_TYPE

    def __init__(self, templateObj):
        TagProcessor.TagProcessor.__init__(self,templateObj)
        self._delimRegexs = self.simpleDirectiveReList(r'set[\f\t ]+(.+?)')
                    
    def translateTag(self, tag):
        """generate python code from setDirective tags, and register the vars with
        placeholderTagProcessor as local vars."""
        templateObj = self.templateObj()

        self.validateTag(tag)
        
        firstEqualSign = tag.find('=')
        varName = tag[0: firstEqualSign].replace(
            self.setting('placeholderStartToken'),'').strip()
        valueString = tag[firstEqualSign+1:]
        valueString = templateObj.translateRawPlaceholderString(valueString)
        # get rid of accidental double calls
        valueString = valueString.replace('()()','()')

        state = self.state()
                
        indent = self.setting('indentationStep')
        if not state.has_key('indentLevel'):
            state['indentLevel'] = \
                        self.setting('initialIndentLevel')
    
        return indent*(state['indentLevel']) + \
               'setVars["""' + varName + '"""]' +\
               "=" + valueString + "\n" + \
               indent * state['indentLevel']
        
