#!/usr/bin/env python
# $Id: IncludeDirective.py,v 1.7 2001/08/15 17:49:51 tavis_rudd Exp $
"""IncludeDirective Processor class Cheetah's codeGenerator

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.7 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/08/15 17:49:51 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.7 $"[11:-2]

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
        
    def preProcess(self, templateDef):
        import Template                         # import it here to avoid circ. imports
            
        RESTART = [False,]
        def subber(match, RESTART=RESTART, Template=Template, self=self):
            args = match.group(1).strip()
    
            # do a safety/security check on this tag
            self.validateTag(args)
            
            includeString = match.group(1).strip()
            
            raw = False
            directInclude = False
    
            ## deal with any extra args to the #include directive
            if args.split()[0] == 'raw':
                raw = True
                args= ' '.join(args.split()[1:])
            elif args.split()[0] == 'direct':
                directInclude = True
                args= ' '.join(args.split()[1:])
                
            ## get the Cheetah code to be included
            if args.startswith( self.setting('placeholderStartToken') ):
                translatedPlaceholder = self.translateRawPlaceholderString(args)
                includeString = self.evalPlaceholderString(translatedPlaceholder)
                
            elif args.startswith('file'):
                args = '='.join(args.split('=')[1:])
                translatedPlaceholder = self.translateRawPlaceholderString(args)
                fileName = self.evalPlaceholderString(translatedPlaceholder)
                fileName = self.normalizePath( fileName )
                includeString = self.getFileContents( fileName )
    
            ## now process finish include
            if raw:            
                includeID = '_' + str(id(includeString)) + str(randrange(10000, 99999))
                self._rawIncludes[includeID] = includeString
                return self.setting('placeholderStartToken') + \
                       '{rawIncludes.' + includeID + '}'
            elif directInclude:
                RESTART[0] = True
                return includeString
            else:
                #@@ autoUpdate behaviour needs to be implemented
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
    
        for RE in self._delimRegexs:
            templateDef = RE.sub(subber, templateDef)
            
        if RESTART[0]:
            return Template.RESTART(templateDef)
        else:
            return templateDef
