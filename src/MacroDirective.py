#!/usr/bin/env python
# $Id: MacroDirective.py,v 1.1 2001/08/11 03:21:35 tavis_rudd Exp $
"""MacroDirective Processor class Cheetah's codeGenerator

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.1 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/08/11 03:21:35 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.1 $"[11:-2]

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

class MacroDirective(TagProcessor.TagProcessor):
    """handle any inline #macro definitions """
    
    def __init__(self, templateObj):
        TagProcessor.TagProcessor.__init__(self,templateObj)


        bits = self._directiveREbits

        gobbleWS = re.compile(bits['start_gobbleWS'] + r'macro[\t ]+' +
                              r'(.+?)' + bits['lazyEndGrp'] + '(.*?)' +
                              bits['lazyEndGrp'] + r'[\f\t ]*#end macro[f\t ]*' +
                              bits['lazyEndGrp'],
                              re.DOTALL | re.MULTILINE)
        
        plain = re.compile(r'#macro[\t ]+' +
                           r'(.+?)(?:/#|\r\n|\n|\r)(.*?)' +
                           r'(?:\r\n|\n|\r)[\t ]*#end macro[\t ]*(?:\r\n|\n|\r|\Z)',
                           re.DOTALL | re.MULTILINE)

        self._delimRegexs = [gobbleWS, plain]
        
    def preProcess(self, templateObj, templateDef):
        
        templateObj = self.templateObj()

        if not hasattr(templateObj, '_macros'):
            templateObj._macros = {}
    
        def handleMacroDefs(match, templateObj=templateObj):
            """process each match of the macro definition regex"""
            macroSignature = match.group(1)
    
            ##validateMacroDirective(templateObj, macroSignature)
            
            firstParenthesis = macroSignature.find('(')
            macroArgstring = macroSignature[firstParenthesis+1:-1]
            macroName = macroSignature[0:firstParenthesis]
    
            argStringChunks = [chunk.strip() for chunk in macroArgstring.split(',')]
            argNamesList = [(chunk.split('='))[0] for chunk in argStringChunks]
            #@@tr: not safe if the default args have commas or = in them!!!
                    
            macroBody = match.group(2).replace("'''","\'\'\'")
    
            def handleArgsUsedInBody(match, argNamesList=argNamesList,
                                     templateObj=templateObj):
                """check each $var in the macroBody to see if it is in this macro's
                argNamesList and needs substituting"""
    
                argName = match.group(1).replace('placeholderTag.','')
                if argName in argNamesList:
                    return "''' + str(" + argName + ") + '''"
    
                ## it's a composite $placeholder so we have to deal with
                # Unified Dotted Notation and autocalling:
                
                firstSpecialChar = re.search(r'\(|\[', argName)
                if firstSpecialChar:         # NameMapper can't handle [] or ()
                    firstSpecialChar = firstSpecialChar.start()
                    nameMapperPartOfName, remainderOfName = \
                                          argName[0:firstSpecialChar], argName[firstSpecialChar:]
                    remainderOfName = remainderOfName
                else:
                    nameMapperPartOfName = argName
                    remainderOfName = ''
    
                ## only do autocalling on names that have no () in them
                if argName.find('(') == -1 and templateObj.setting('useAutocalling'):
                    safeToAutoCall = True
                else:
                    safeToAutoCall = False
    
                nameMapperChunks = nameMapperPartOfName.split('.')
                if nameMapperChunks[0] in argNamesList:
                    return "''' + str(NameMapper.valueForName(" + nameMapperChunks[0] + ", '" +\
                           '.'.join(nameMapperChunks[1:]) + "', executeCallables=" + \
                           str(safeToAutoCall) + ")" + remainderOfName + ") + '''"
                else:
                    return templateObj.setting('placeholderStartToken') + \
                           '{' + match.group(1) + '}'
    
            processor = templateObj.placeholderProcessor
    
            macroBody = processor.wrapExressionsInStr(processor.markPlaceholders(macroBody),
                                                      marker=templateObj.setting('placeholderMarker'),
                                                      before='<argInBody>',
                                                      after='</argInBody>')
    
            regex = re.compile(r'<argInBody>(.*?)</argInBody>')
            macroBody = regex.sub(handleArgsUsedInBody,macroBody )
    
            if macroName not in vars().keys():
                macroFuncName =  macroName
            else:
                macroFuncName =  'macroFunction'
                
            macroCode = "def " + macroFuncName + "(" + macroArgstring + "):\n" + \
                        "    return '''" + macroBody + "'''\n"
    
            exec macroCode in None, None
            exec "templateObj._macros[macroName] = " + macroFuncName in vars()
            
            return ''


        
        ##
        for RE in self._delimRegexs:
            templateDef = RE.sub(handleMacroDefs, templateDef)
        return templateDef
