#!/usr/bin/env python
# $Id: DisplayLogic.py,v 1.3 2001/08/13 01:58:28 tavis_rudd Exp $
"""DisplayLogic Processor class Cheetah's codeGenerator

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.3 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/08/13 01:58:28 $
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

class DisplayLogic(TagProcessor.TagProcessor):
    """A class for processing display logic tags in Cheetah Templates."""
    _token = 'displayLogic'
    _tagType = TagProcessor.EXEC_TAG_TYPE
    
    def __init__(self, templateObj):
        TagProcessor.TagProcessor.__init__(self, templateObj)

        bits = self._directiveREbits
        anythingBut = r'[^(?:' + bits['endTokenEsc'] + r')]+?' # anything but the endToken
        gobbleWS = re.compile(bits['start_gobbleWS'] + r'(' +
                              r'if[\f\t ]+' + anythingBut + '|' +
                              r'else[\f\t ]*?|' +
                              r'else[\f\t ]if[\t ]+' + anythingBut + '|' +
                              r'elif[\f\t ]+' + anythingBut + '|' +
                              r'for[\f\t ]+' + anythingBut + '|' +
                              r'continue|' +
                              r'break|' +
                              r'end[\f\t ]+if|' +
                              r'end[\f\t ]+for|' +
                              r')[\f\t ]*' + bits['lazyEndGrp'],
                              re.MULTILINE
                              )
        
        plain =  re.compile(bits['start'] + r'(' +
                            r'if[\f\t ]+.+?|' +
                            r'else[\f\t ]*?|' +
                            r'else[\f\t ]if[\f\t ]+.+?|' +
                            r'elif[\f\t ]+.+?|' +
                            r'for[\f\t ].+?|' +
                            r'end[\f\t ]+if|' +
                            r'end[\f\t ]+for|' +
                            r')[\f\t ]*' + bits['endGrp'],
                            re.MULTILINE
                            )

        self._delimRegexs = [gobbleWS, plain]
                    
    def translateTag(self, tag):
        """process display logic embedded in the template"""

        templateObj = self.templateObj()
        settings = templateObj._settings
        state = self.state()
        indent = settings['indentationStep']
        
        tag = tag.strip()
        self.validateTag(tag) 
        
        if tag in ('end if','end for'):
            state['indentLevel'] -= 1
            outputCode = indent*state['indentLevel']

        elif tag in ('continue','break'):
            outputCode = indent*state['indentLevel'] + tag \
                         + "\n" + \
                         indent*state['indentLevel']
        elif tag[0:4] in ('else','elif'):
            tag = tag.replace('else if','elif')
            
            if tag[0:4] == 'elif':
                tag = templateObj.translateRawPlaceholderString(tag)
                tag = tag.replace('()() ','() ') # get rid of accidental double calls
            
            outputCode = indent*(state['indentLevel']-1) + \
                         tag +":\n" + \
                         indent*state['indentLevel']
    
        elif tag.startswith('if ') or tag.startswith('for '): # it's the start of a new block
            state['indentLevel'] += 1
            
            if tag[0:3] == 'for':
                ##translate this #for $i in $list/# to this #for i in $list/#
                INkeywordPos = tag.find(' in ')
                tag = tag[0:INkeywordPos].replace(
                    self.setting('placeholderStartToken'),'') + \
                               tag[INkeywordPos:]
    
                ## register the local vars in the loop with the templateObj  ##
                #  so placeholderTagProcessor will recognize them
                #  and handle their use appropriately
                localVars, restOfForStatement = tag[3:].split(' in ')
                localVarsList =  [localVar.strip() for localVar in
                                  localVars.split(',')]
                templateObj._localVarsList += localVarsList 
    
            tag = templateObj.translateRawPlaceholderString(tag)
            tag = tag.replace('()() ','() ') # get rid of accidental double calls
            outputCode = indent*(state['indentLevel']-1) + \
                         tag + ":\n" + \
                         indent*state['indentLevel']
        
        else:                           # it's a chunk of plain python code              
            outputCode = indent*(state['indentLevel']) + \
                         tag + \
                         "\n" + indent*state['indentLevel']            
            
        return outputCode
