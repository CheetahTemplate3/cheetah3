#!/usr/bin/env python
# $Id: MacroDirective.py,v 1.6 2001/08/13 22:01:28 tavis_rudd Exp $
"""MacroDirective Processor class Cheetah's codeGenerator

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.6 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/08/13 22:01:28 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.6 $"[11:-2]

##################################################
## DEPENDENCIES ##

import re

# intra-package imports ...
import TagProcessor
from NameMapper import valueFromSearchList, valueForName
import NameMapper
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
                              bits['lazyEndGrp'] + r'[\f\t ]*' +
                              bits['startTokenEsc'] + 'end macro[f\t ]*' +
                              bits['lazyEndGrp'],
                              re.DOTALL | re.MULTILINE)
        
        plain = re.compile(bits['start'] + r'macro[\t ]+' +
                           r'(.+?)' + bits['endGrp'] + '(.*?)' +
                           bits['lazyEndGrp'] + r'[\f\t ]*' +
                           bits['startTokenEsc'] + 'end macro[\t ]*' +
                           bits['endGrp'],
                           re.DOTALL | re.MULTILINE)

        self._delimRegexs = [gobbleWS, plain]

        
    def preProcess(self, templateDef):
        
        templateObj = self.templateObj()

        if not hasattr(templateObj, '_macros'):
            templateObj._macros = {}
    
        def handleMacroDefs(match, self=self, templateObj=templateObj):
            """process each match of the macro definition regex"""
            macroSignature = match.group(1)

            ##validateMacroDirective(templateObj, macroSignature)
            
            firstParenthesis = macroSignature.find('(')
            macroName = macroSignature[0:firstParenthesis]
            macroArgstring = macroSignature[firstParenthesis:]

            dummyCode = 'def dummy' + macroArgstring + ': pass'
            globalsDict, localsDict = self.execPlaceholderString(dummyCode)
            argNamesList = localsDict['dummy'].func_code.co_varnames

            macroBody = match.group(2).replace("'''","\'\'\'")
    
            def handleArgsUsedInBody(match, argNamesList=argNamesList,
                                     templateObj=templateObj):
                """check each $var in the macroBody to see if it is in this macro's
                argNamesList and needs substituting"""

                from NameMapper import valueFromSearchList, valueForName
                
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
                
            macroCode = "def " + macroFuncName + macroArgstring + ":\n" + \
                        "    return '''" + macroBody + "'''\n"
    
            exec macroCode in None, None
            exec "templateObj._macros[macroName] = " + macroFuncName in vars()
            
            return ''


        
        ##
        for RE in self._delimRegexs:
            templateDef = RE.sub(handleMacroDefs, templateDef)
        return templateDef




class CallMacroDirective(TagProcessor.TagProcessor):
    """handle any  #callMacro definitions """
    
    def __init__(self, templateObj):
        TagProcessor.TagProcessor.__init__(self,templateObj)

        bits = self._directiveREbits
        plain =  re.compile(bits['start'] + r'callMacro[\t ]+' +
                            r'(?P<macroName>[A-Za-z_][A-Za-z_0-9]*?)' +
                            r'\((?P<argString>.*?)\)[\t ]*' + bits['endGrp'] +
                            r'(?P<extendedArgString>.*?)' +
                            bits['startTokenEsc'] + r'end callMacro[\t ]*' + bits['endGrp'],
                            re.DOTALL | re.MULTILINE)

        self._argsRE = re.compile(bits['start'] + r'arg[\t ]+' +
                                  r'(?P<argName>[A-Za-z_][A-Za-z_0-9]*?)' +
                                  r'[\t ]*' + bits['endGrp'] +
                                  r'(?P<argValue>.*?)' +
                                  r'(?:\r\n|\n|\r)[\t ]*' + 
                                  bits['startTokenEsc'] + 'end arg[\t ]*'
                                  + bits['endGrp'],
                            re.DOTALL | re.MULTILINE)

        self._delimRegexs = [plain, ]
        
    def preProcess(self, templateDef):
        templateObj = self.templateObj()

        def subber(match, templateObj=templateObj,
                   argsRE=self._argsRE):
            
            macroName = match.group('macroName').strip()
            argString = match.group('argString')
            extendedArgString = match.group('extendedArgString')
    
            try:
                searchList = templateObj.searchList()
                argString = templateObj.translateRawPlaceholderString(argString)
                
            except NameMapper.NotFound, name:
                line = lineNumFromPos(match.string, match.start())
                raise Error('Undeclared variable ' + str(name) + 
                            ' used in macro call #'+ macroSignature + 
                            ' on line ' + str(line))
    
            extendedArgsDict = {}
            
            def processExtendedArgs(match, extendedArgsDict=extendedArgsDict):
                """check each $var in the macroBody to see if it is in this macro's
                argNamesList and needs substituting"""
                extendedArgsDict[ match.group('argName') ] = match.group('argValue')
                return ''
    

            argsRE.sub(processExtendedArgs, extendedArgString)
    
            
            fullArgString = argString
            if fullArgString:
                fullArgString += ', '
            for argName in extendedArgsDict.keys():
                fullArgString += argName + '=extendedArgsDict["' + argName + \
                                 '"]' + ', '
            
            ## validateMacroDirective(templateObj, fullArgString)
                
            if macroName in templateObj._macros.keys():
                return eval('templateObj._macros[macroName](' + fullArgString + ')', vars())
            else:
                raise Error('The macro ' + macroName + \
                            ' was called, but it does not exist')
            
        for RE in self._delimRegexs:
            templateDef = RE.sub(subber, templateDef)
    
        return templateDef



class LazyMacroCall(TagProcessor.TagProcessor):
    """Handle any calls to macros that are already defined."""
    
    def __init__(self, templateObj):
        TagProcessor.TagProcessor.__init__(self,templateObj)
        from Parser import escCharLookBehind
        bits = self._directiveREbits
        plain = re.compile(escCharLookBehind + r'(#[a-zA-Z_][a-zA-Z_0-9\.]*\(.*?\))')
        self._delimRegexs = [plain]
        
    def preProcess(self, templateDef):
        
        templateObj = self.templateObj()
        
        def handleMacroCalls(match, self=self, templateObj=templateObj):
            """for each macro call that is found in the template, substitute it with
            the macro's output"""

            from NameMapper import valueFromSearchList, valueForName
            
            macroSignature = match.group(1)[1:]
            firstParenthesis = macroSignature.find('(')
            macroArgstring = macroSignature[firstParenthesis+1:-1]
            macroName = macroSignature[0:firstParenthesis]
    
            searchList = templateObj.searchList()
            
            try:
                macroArgstring = self.translateRawPlaceholderString(macroArgstring)
            except NameMapper.NotFound, name:
                line = lineNumFromPos(match.string, match.start())
                raise Error('Undeclared variable ' + str(name) + \
                            ' used in macro call #'+ macroSignature + ' on line ' +
                            str(line))       
                
            ## validateMacroDirective(templateObj, macroArgstring)
            
            if macroName in templateObj._macros.keys():
    
                return eval('templateObj._macros[macroName](' + macroArgstring + ')',
                            vars())
            else:
                raise Error('The macro ' + macroName + \
                            ' was called, but it does not exist')
    
        for RE in self._delimRegexs:
            templateDef = RE.sub(handleMacroCalls, templateDef)
        return templateDef
