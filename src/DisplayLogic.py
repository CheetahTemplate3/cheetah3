#!/usr/bin/env python
# $Id: DisplayLogic.py,v 1.6 2001/09/10 02:37:45 tavis_rudd Exp $
"""DisplayLogic Processor class Cheetah's codeGenerator

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.6 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/09/10 02:37:45 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.6 $"[11:-2]

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

        reTemplate = (r'%(startGrp)s(' +
                      r'if[\f\t ]+%(content)s|' +
                      r'else[\f\t ]*?|' +
                      r'else[\f\t ]if[\t ]+%(content)s|' +
                      r'elif[\f\t ]+%(content)s|' +
                      r'end[\f\t ]+if|' +
                      r'for[\f\t ]+%(content)s|' +
                      r'end[\f\t ]+for|' +
                      r'while[\f\t ]+%(content)s|' +
                      r'end[\f\t ]+while|' +
                      r'continue|' +
                      r'break|' +
                      r'try[\f\t ]*?|' +
                      r'except[\f\t ]*?|' +
                      r'except[\f\t ]+%(content)s|' +
                      r'finally[\f\t ]*?|' +
                      r'end[\f\t ]+try|' +
                      r'raise[\f\t ]+%(content)s|' +
                      r')[\f\t ]*%(endGrp)s')
            
        plain = re.compile(
            reTemplate %
            {'startGrp':bits['start'],
             'content': r'.+?', # anything 
             'endGrp': bits['endGrp'],
             },
            re.MULTILINE)
        
        gobbleWS = re.compile(
            reTemplate %
            {'startGrp':bits['start_gobbleWS'],
             'content': r'[^(?:' + bits['endTokenEsc'] + r')]+?', # anything but the endToken
             'endGrp': bits['lazyEndGrp'],
             },
            re.MULTILINE)

        self._delimRegexs = [gobbleWS, plain]
                    
    def translateTag(self, tag):
        """process display logic embedded in the template"""

        settings = self.settings()
        state = self.state()
        indent = settings['indentationStep']
        
        tag = tag.strip()
        self.validateTag(tag) 
        
        if tag.startswith('end'):
            state['indentLevel'] -= 1
            outputCode = indent*state['indentLevel']
            
        elif (tag.startswith('if') or tag.startswith('for') or 
              tag.startswith('while') or tag.startswith('try')):
            # it's the start of a new block
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
                self._localVarsList.extend(localVarsList)
    
            tag = self.translateRawPlaceholderString(tag)
            tag = tag.replace('()() ','() ') # get rid of accidental double calls
            outputCode = indent*(state['indentLevel']-1) + \
                         tag + ":\n" + \
                         indent*state['indentLevel']
            
        elif (tag.startswith('else') or tag.startswith('elif') or
              tag.startswith('except') or tag.startswith('finally')):
            
            tag = tag.replace('else if','elif')
            tag = self.translateRawPlaceholderString(tag)
            tag = tag.replace('()() ','() ') # get rid of accidental double calls            

            outputCode = indent*(state['indentLevel']-1) + \
                         tag +":\n" + \
                         indent*state['indentLevel']
    
        else:
            # it's a chunk of plain python code: while, continue, raise, etc.
            tag = self.translateRawPlaceholderString(tag)
            outputCode = indent*state['indentLevel'] + tag + \
                         "\n" + indent*state['indentLevel']            
            
        return outputCode
