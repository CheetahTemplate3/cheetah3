#!/usr/bin/env python
# $Id: DisplayLogicProcessor.py,v 1.1 2001/08/10 19:26:02 tavis_rudd Exp $
"""DisplayLogicProcessor class Cheetah's codeGenerator

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.1 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/08/10 19:26:02 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.1 $"[11:-2]

##################################################
## DEPENDENCIES ##

# intra-package imports ...
import TagProcessor
from Delimiters import delimiters

##################################################
## CONSTANTS & GLOBALS ##

True = (1==1)
False = (0==1)

##################################################
## CLASSES ##

class Error(Exception):
    pass

class DisplayLogicProcessor(TagProcessor.TagProcessor):
    """A class for processing display logic tags in Cheetah Templates."""
    
    def __init__(self, templateObj):
        TagProcessor.TagProcessor.__init__(self, templateObj)
        self._tagType = TagProcessor.EXEC_TAG_TYPE
        self._delimRegexs = [delimiters['displayLogic_gobbleWS'],
                             delimiters['displayLogic']]
        self._token = 'displayLogic'
                    
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
                tag = templateObj.translatePlaceholderVars(tag)
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
    
            tag = templateObj.translatePlaceholderVars(tag)
            tag = tag.replace('()() ','() ') # get rid of accidental double calls
            outputCode = indent*(state['indentLevel']-1) + \
                         tag + ":\n" + \
                         indent*state['indentLevel']
        
        else:                           # it's a chunk of plain python code              
            outputCode = indent*(state['indentLevel']) + \
                         tag + \
                         "\n" + indent*state['indentLevel']            
            
        return outputCode
