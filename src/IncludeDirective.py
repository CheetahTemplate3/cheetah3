#!/usr/bin/env python
# $Id: IncludeDirective.py,v 1.14 2001/09/17 06:04:40 tavis_rudd Exp $
"""IncludeDirective Processor class Cheetah's codeGenerator

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.14 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/09/17 06:04:40 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.14 $"[11:-2]

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

        self._token = 'includeDirective'
        bits = self._directiveREbits
        gobbleWS = re.compile(bits['start_gobbleWS'] + r'include[\t ]+' +
                              r'([^(?:/#)]+?)' +
                              bits['lazyEndGrp'],
                              re.MULTILINE)
        plain = re.compile(bits['start'] +
                           r'include[\t ]+(.+?)' +
                           bits['endGrp'])

        self._delimRegexs = [gobbleWS, plain]


        
    def processTag(self, tag):
        """

        #include <ARGS> <EXPR>
        ... uses the value of EXPR as the path of the file to include.

        #include <ARGS> source = <EXPR> 
        ... includes the value of the EXPR 

        where <ARGS> is 'raw' or 'direct'
        """
        EXPR = tag

        # do a safety/security check on this tag
        self.validateTag(EXPR)
        
        includeString = EXPR
        
        raw = False
        includeFrom = 'file'
        
        ## deal with any extra args to the #include directive
        if EXPR.split()[0] == 'raw':
            raw = True
            EXPR= ' '.join(EXPR.split()[1:])
        elif EXPR.split()[0] == 'direct':
            directInclude = True
            EXPR= ' '.join(EXPR.split()[1:])
            

        if EXPR.startswith('source'): # include the value of the EXPR 
            includeFrom = 'str'
            EXPR = '='.join(EXPR.split('=')[1:])
            
        translatedPlaceholder = self.translateRawPlaceholderString(EXPR)

        ## now process finish include
        indent = self.setting('indentationStep')
        return self.wrapExecTag(
            indent*self.state()['indentLevel'] +
            'includeCheetahSource('+ translatedPlaceholder + 
            ', trans, includeFrom="' + includeFrom + '", raw=' + str(raw) + ')\n'
            + indent*self.state()['indentLevel'] )
    
    def __processTag(self, templateDef):
        import Template                         # import it here to avoid circ. imports
        self.RESTART = False

        for RE in self._delimRegexs:
            templateDef = RE.sub(self.handleInclude, templateDef)
            
        if self.RESTART:
            self.RESTART = False
            return Template.RESTART(templateDef)
        else:
            return templateDef
