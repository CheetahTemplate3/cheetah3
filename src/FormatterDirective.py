#!/usr/bin/env python
# $Id: FormatterDirective.py,v 1.1 2001/08/13 01:57:44 tavis_rudd Exp $
"""FormatterDirective Processor class Cheetah's codeGenerator

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.1 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/08/13 01:57:44 $
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

class FormatterDirective(TagProcessor.TagProcessor):
    """A class for processing display logic tags in Cheetah Templates."""
    
    _token = 'formatterDirective'
    _tagType = TagProcessor.EXEC_TAG_TYPE

    def __init__(self, templateObj):
        TagProcessor.TagProcessor.__init__(self,templateObj)
        self._delimRegexs = self.simpleDirectiveReList(r'formatter[\f\t ]+(.+?)')
                    
    def translateTag(self, tag):
        """generate python code from setDirective tags, and register the vars with
        placeholderTagProcessor as local vars."""
        templateObj = self.templateObj()
        state = self.state()
        self.validateTag(tag)
        
        interactive = False
        tagChunks = tag.split()
        if tagChunks[0].lower().startswith('interactive'):
            interactive = True
            tag = ' '.join(tagChunks[1:])

        if tagChunks[0].lower().startswith('default'):
            state['interactiveFormatter'] = self.setting('interactiveFormatter')
            state['currFormatter'] = currFormatter = 'default'

        else:
            valueString = self.translateRawPlaceholderString(tag, autoCall=False)
            formatter = self.evalPlaceholderString(valueString)
            state['interactiveFormatter'] = interactive
            state['currFormatter'] = currFormatter = str(id(formatter))
            self.settings()['theFormatters'][currFormatter] = formatter
        
        indent = self.setting('indentationStep')
        if not state.has_key('indentLevel'):
            state['indentLevel'] = \
                        self.setting('initialIndentLevel')

        return indent*(state['indentLevel']) + \
               'format = self.setting("theFormatters")["' + currFormatter + '"]' + "\n" + \
               indent * state['indentLevel']
        
