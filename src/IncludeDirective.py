#!/usr/bin/env python
# $Id: IncludeDirective.py,v 1.10 2001/08/17 15:48:55 tavis_rudd Exp $
"""IncludeDirective Processor class Cheetah's codeGenerator

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.10 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/08/17 15:48:55 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.10 $"[11:-2]

##################################################
## DEPENDENCIES ##

import re
from random import randrange

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

class IncludeDirective(TagProcessor.TagProcessor):

    def __init__(self, templateObj):
        """Replace any #include statements with their substitution value.  This
        method can handle includes from file and from placeholders such as
        $getBodyTemplate"""

        TagProcessor.TagProcessor.__init__(self,templateObj)
        
        bits = self._directiveREbits
        gobbleWS = re.compile(bits['start_gobbleWS'] + r'include[\t ]+' +
                              r'([^(?:/#)]+?)' +
                              bits['lazyEndGrp'],
                              re.MULTILINE)
        plain = re.compile(bits['start'] +
                           r'include[\t ]+(.+?)' +
                           bits['endGrp'])

        self._delimRegexs = [gobbleWS, plain]

        
    def handleInclude(self, match):
        """

        #include <ARGS> <EXPR> 
        ... includes the value of the EXPR 
        
        #include <ARGS> file = <EXPR> 
        ... uses the value of EXPR as the path of the file to  include.

        where <ARGS> is 'raw' or 'direct'
        """
        
        import Template
        EXPR = match.group(1).strip()

        # do a safety/security check on this tag
        self.validateTag(EXPR)
        
        includeString = match.group(1).strip()
        
        raw = False
        directInclude = False
        includeFromFile = False
        
        ## deal with any extra args to the #include directive
        if EXPR.split()[0] == 'raw':
            raw = True
            EXPR= ' '.join(EXPR.split()[1:])
        elif EXPR.split()[0] == 'direct':
            directInclude = True
            EXPR= ' '.join(EXPR.split()[1:])
            
        ## get the path of the Cheetah code to be included or the code itself
        if EXPR.startswith('file'):
            includeFromFile = True
            EXPR = '='.join(EXPR.split('=')[1:])
            translatedPlaceholder = self.translateRawPlaceholderString(EXPR)
            fileName = self.evalPlaceholderString(translatedPlaceholder)
            fileName = self.normalizePath( fileName )
            if directInclude or raw:
                includeString = self.getFileContents( fileName )
        else:                           # include the value of the 
            translatedPlaceholder = self.translateRawPlaceholderString(EXPR)
            includeString = self.evalPlaceholderString(translatedPlaceholder)
            

        ## now process finish include
        if raw:            
            includeID = '_' + str(id(includeString)) + str(randrange(10000, 99999))
            self._rawIncludes[includeID] = includeString
            return self.setting('placeholderStartToken') + \
                   '{rawIncludes.' + includeID + '}'
        elif directInclude:
            self.RESTART = True
            return includeString
        elif includeFromFile:
            includeID = '_' + str(id(fileName))
            nestedTemplate = Template.Template(
                templateDef=None,
                file=fileName,
                overwriteSettings=self.settings(),
                preBuiltSearchList=self.searchList(),
                setVars = self._setVars,
                cheetahBlocks=self._cheetahBlocks,
                macros=self._macros,
                )
        else:
            includeID = '_' + str(id(includeString))
            nestedTemplate = Template.Template(
                templateDef=includeString,
                overwriteSettings=self.settings(),
                preBuiltSearchList=self.searchList(),
                setVars = self._setVars,
                cheetahBlocks=self._cheetahBlocks,
                macros=self._macros,
                )
            
        self._parsedIncludes[includeID] = nestedTemplate
        if not hasattr(nestedTemplate, 'respond'):
            nestedTemplate.compileTemplate()
        return self.setting('placeholderStartToken') + \
               '{parsedIncludes.' + includeID + '.respond(trans, iAmNested=True)}'
    
    def preProcess(self, templateDef):
        import Template                         # import it here to avoid circ. imports
        self.RESTART = False

        for RE in self._delimRegexs:
            templateDef = RE.sub(self.handleInclude, templateDef)
            
        if self.RESTART:
            self.RESTART = False
            return Template.RESTART(templateDef)
        else:
            return templateDef
