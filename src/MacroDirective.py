#!/usr/bin/env python
# $Id: MacroDirective.py,v 1.8 2001/08/16 22:15:18 tavis_rudd Exp $
"""MacroDirective Processor class Cheetah's codeGenerator

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.8 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/08/16 22:15:18 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.8 $"[11:-2]

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
        reChunk = 'macro[\f\t ]+(?P<macroSignature>.+?)'
        self._startTagRegexs = self.simpleDirectiveReList(reChunk)
        self._endTagRE = re.compile(bits['start_gobbleWS'] + r'end[\f\t ]+macro[\f\t ]*' + 
                                    bits['lazyEndGrp'] + '|'+
                                    bits['start'] + r'end[\f\t ]+macro[\f\t ]*' +
                                    bits['endGrp'],
                                    re.DOTALL | re.MULTILINE)


    def handleMacroDefs(self, startTagMatch, templateDef):
        """process each match of the macro definition regex"""
                                                      
        endTagMatch = self._endTagRE.search(templateDef)
        if not endTagMatch:
            raise Error("Cheetah couldn't find an end tag for the #macro directive at\n" +
                        "position " + str(startTagMatch.start()) + " in the template definition.")
        
        macroSignature = startTagMatch.group('macroSignature')            
        macroBody = templateDef[startTagMatch.end() : endTagMatch.start()]
        macroBody = macroBody.replace("'''","\'\'\'")
        macroBody = macroBody.replace("'''","\'\'\'")
        self.validateTag(macroSignature)
        
        firstParenthesis = macroSignature.find('(')
        macroName = macroSignature[0:firstParenthesis]
        macroArgstring = macroSignature[firstParenthesis:]

        dummyCode = 'def dummy' + macroArgstring + ': pass'
        globalsDict, localsDict = self.execPlaceholderString(dummyCode)
        argNamesList = localsDict['dummy'].func_code.co_varnames

        macroBody = self.wrapExressionsInStr(self.markPlaceholders(macroBody),
                                             marker=self.setting('placeholderMarker'),
                                             before='<argInBody>',
                                             after='</argInBody>')        
        
        regex = re.compile(r'<argInBody>(.*?)</argInBody>')
        self._argNamesList = argNamesList
        macroBody = regex.sub(self.handleArgsUsedInBody, macroBody)
        del self._argNamesList
        
        if macroName not in vars().keys():
            macroFuncName =  macroName
        else:
            macroFuncName =  'macroFunction'
            
        macroCode = "def " + macroFuncName + macroArgstring + ":\n" + \
                    "    return '''" + macroBody + "'''\n"

        exec macroCode in None, None
        exec "self._macros[macroName] = " + macroFuncName in vars()


        return templateDef[0:startTagMatch.start()] + templateDef[endTagMatch.end():]
        #end handleMacroDef()
        

    def handleArgsUsedInBody(self, match):
        """check each $var in the macroBody to see if it is in this macro's
        argNamesList and needs substituting"""

        argNamesList = self._argNamesList
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
        if argName.find('(') == -1 and self.setting('useAutocalling'):
            safeToAutoCall = True
        else:
            safeToAutoCall = False

        nameMapperChunks = nameMapperPartOfName.split('.')
        if nameMapperChunks[0] in argNamesList:
            return "''' + str(NameMapper.valueForName(" + nameMapperChunks[0] + ", '" +\
                   '.'.join(nameMapperChunks[1:]) + "', executeCallables=" + \
                   str(safeToAutoCall) + ")" + remainderOfName + ") + '''"
        else:
            return self.setting('placeholderStartToken') + \
                   '{' + match.group(1) + '}'
        
        #end handleArgsUsedInBody()

        
    def preProcess(self, templateDef):
        for startTagRE in self._startTagRegexs:
            while startTagRE.search(templateDef):
                startTagMatch = startTagRE.search(templateDef)
                templateDef = self.handleMacroDefs(startTagMatch=startTagMatch,
                                                   templateDef=templateDef)
        
        return templateDef




class CallMacroDirective(TagProcessor.TagProcessor):
    """handle any  #callMacro definitions """
    
    def __init__(self, templateObj):
        TagProcessor.TagProcessor.__init__(self,templateObj)



        bits = self._directiveREbits
        reChunk = r'callMacro[\f\t ]+' + \
                  r'(?P<macroName>[A-Za-z_][A-Za-z_0-9]*?)' + \
                  r'\((?P<argString>.*?)\)[\f\t ]*'
        
        self._startTagRegexs = self.simpleDirectiveReList(reChunk)
        
        self._endTagRE = re.compile(bits['start_gobbleWS'] + r'end[\f\t ]+callMacro[\f\t ]*' + 
                                    bits['lazyEndGrp'] + '|'+
                                    bits['start'] + r'end[\f\t ]+callMacro[\f\t ]*' +
                                    bits['endGrp'],
                                    re.DOTALL | re.MULTILINE)

        self._argsRE = re.compile(bits['start'] + r'arg[\t ]+' +
                                  r'(?P<argName>[A-Za-z_][A-Za-z_0-9]*?)' +
                                  r'[\t ]*' + bits['endGrp'] +
                                  r'(?P<argValue>.*?)' +
                                  r'(?:\r\n|\n|\r)[\t ]*' + 
                                  bits['startTokenEsc'] + 'end arg[\t ]*'
                                  + bits['endGrp'],
                            re.DOTALL | re.MULTILINE)


    def handleCallMacroDirective(self, startTagMatch, templateDef):

        endTagMatch = self._endTagRE.search(templateDef)
        if not endTagMatch:
            raise Error(
                "Cheetah couldn't find an end tag for the #callMacro directive at\n" +
                "position " + str(startTagMatch.start()) +
                " in the template definition.")

        macroName = startTagMatch.group('macroName')
        argString = startTagMatch.group('argString')            
        extendedArgString = templateDef[startTagMatch.end() : endTagMatch.start()]


        try:
            searchList = self.searchList()
            argString = self.translateRawPlaceholderString(argString)
            
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


        self._argsRE.sub(processExtendedArgs, extendedArgString)

        
        fullArgString = argString
        if fullArgString:
            fullArgString += ', '
        for argName in extendedArgsDict.keys():
            fullArgString += argName + '=extendedArgsDict["' + argName + \
                             '"]' + ', '
        
        self.validateTag(fullArgString)
            
        if macroName in self._macros.keys():
            replacementStr = self.evalPlaceholderString(
                'macros["' + macroName + '"](' + fullArgString + ')',
                localsDict={'macros':self._macros,
                            'extendedArgsDict':extendedArgsDict})
            return templateDef[0:startTagMatch.start()] + replacementStr + \
                   templateDef[endTagMatch.end():]
        else:
            raise Error('The macro ' + macroName + \
                        ' was called, but it does not exist')
        
        # end handleCallMacroDirective()
        
    def preProcess(self, templateDef):
        for startTagRE in self._startTagRegexs:
            while startTagRE.search(templateDef):
                startTagMatch = startTagRE.search(templateDef)
                templateDef = self.handleCallMacroDirective(startTagMatch=startTagMatch,
                                                            templateDef=templateDef)
        return templateDef

class LazyMacroCall(TagProcessor.TagProcessor):
    """Handle any calls to macros that are already defined."""
    
    def __init__(self, templateObj):
        TagProcessor.TagProcessor.__init__(self,templateObj)
        
        from Parser import escCharLookBehind
        startToken = self.setting('directiveStartToken')
        self._macroRE = re.compile(escCharLookBehind + startToken +
                                   r'([a-zA-Z_][a-zA-Z_0-9\.]*)\(')


    def handleMacroCall(self, macroCall):
        """for each macro call that is found in the template, substitute it with
        the macro's output"""

        from NameMapper import valueFromSearchList, valueForName
        
        firstParenthesis = macroCall.find('(')
        macroArgstring = macroCall[firstParenthesis+1:-1]
        macroName = macroCall[0:firstParenthesis]

        if not macroName in self._macros.keys():
            return self.setting('directiveStartToken') + macroCall

        self.validateTag(macroArgstring)
        
        try:
            macroArgstring = self.translateRawPlaceholderString(macroArgstring)
        except NameMapper.NotFound, name:
            raise Error('Undeclared variable ' + str(name) + \
                        ' used in macro call #'+ macroCall)


        return self.evalPlaceholderString(
            'macros["' + macroName + '"](' + macroArgstring + ')',
            localsDict={'macros':self._macros})
    
        # end handleMacroCall()
    
    def preProcess(self, templateDef):
        MARKER = ' macroCall.'
        macroRE = self._macroRE
        while macroRE.search(templateDef):
            tempTD = macroRE.sub(MARKER + r'\1(', templateDef)
            tempTD = self.markPlaceholders(tempTD)
            result = []
            resAppend = result.append
            for live, chunk in self.splitExprFromTxt(tempTD, MARKER):
                if live:
                    resAppend( self.handleMacroCall(chunk) )
                else:
                    resAppend(chunk)
                    
            templateDef = ''.join(result)
           
        return self.unmarkPlaceholders(templateDef)


