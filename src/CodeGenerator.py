#!/usr/bin/env python
# $Id: CodeGenerator.py,v 1.28 2001/08/10 22:44:36 tavis_rudd Exp $
"""Utilities, processors and filters for Cheetah's codeGenerator

Cheetah's codeGenerator is designed to be extensible with plugin
functions.  This module contains the default plugins.

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.28 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2001/08/10 22:44:36 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.28 $"[11:-2]

##################################################
## DEPENDENCIES ##

import re
import types
from time import time as currentTime # used in the cache refresh code

# intra-package imports ...
import TagProcessor
import NameMapper
from Delimiters import delimiters
#import Template #NOTE THIS IS IMPORTED BELOW TO AVOID CIRCULAR IMPORTS
from Utilities import lineNumFromPos

##################################################
## CONSTANTS & GLOBALS ##

True = (1==1)
False = (0==1)

##################################################
## CLASSES ##

class Error(Exception):
    pass

class NoDefault:
    pass


##################################################
## FUNCTIONS ##

## codeGenerator plugins ##

def preProcessComments(templateObj, templateDef):
    """cut comments out of the templateDef"""
    def subber(match):
        #commentString = match.group(1)
        return ''
    
    for regex in templateObj._settings['delimiters']['comments']:
        templateDef = regex.sub(subber, templateDef)
        
    return templateDef

def preProcessSlurpDirective(templateObj, templateDef):
    """cut #slurp's out of the templateDef"""
    def subber(match):
        return ''
    
    for regex in templateObj._settings['delimiters']['slurp']:
        templateDef = regex.sub(subber, templateDef)
    return templateDef

def preProcessDataDirectives(templateObj, templateDef):

    def dataDirectiveProcessor(match, templateObj=templateObj):
        """process any #data directives that are found in the template
        extension"""
        
        args = match.group('args').split(',')
        contents = match.group('contents')
        
        newDataDict = {'self':templateObj}
        exec contents in {}, newDataDict

        del newDataDict['self']
        if not 'nomerge' in args:
            templateObj.mergeNewTemplateData(newDataDict)
        else:
            for key, val in newDataDict.items():
                setattr(templateObj,key,val)
            
        return '' # strip the directive from the extension

    for RE in templateObj._settings['delimiters']['dataDirective']:
        templateDef = RE.sub(dataDirectiveProcessor, templateDef)
    return templateDef

def preProcessMacroDirectives(templateObj, templateDef):
    """handle any inline #macro definitions """ 
    
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

    for RE in templateObj._settings['delimiters']['macroDirective']:
        templateDef = RE.sub(handleMacroDefs, templateDef)
    return templateDef

def preProcessLazyMacroCalls(templateObj, templateDef):
    """Handle any calls to macros that are already defined."""
    
    def handleMacroCalls(match, templateObj=templateObj):
        """for each macro call that is found in the template, substitute it with
        the macro's output"""
        
        macroSignature = match.group(1)[1:]
        firstParenthesis = macroSignature.find('(')
        macroArgstring = macroSignature[firstParenthesis+1:-1]
        macroName = macroSignature[0:firstParenthesis]

        searchList = templateObj.searchList()
        searchList_getMeth = searchList.get # shortcut name-binding in the eval
        
        try:
            macroArgstring = templateObj.translatePlaceholderVars(macroArgstring)
            
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

    for RE in templateObj._settings['delimiters']['lazyMacroCalls']:
        templateDef = RE.sub(handleMacroCalls, templateDef)
    return templateDef


def preProcessExplicitMacroCalls(templateObj, templateDef):
    """process the explicit callMacro directives"""
    
    def subber(match, templateObj=templateObj):
        macroName = match.group('macroName').strip()
        argString = match.group('argString')
        extendedArgString = match.group('extendedArgString')

        try:
            searchList = templateObj.searchList()
            argString = templateObj.translatePlaceholderVars(argString)
            
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

        regex = templateObj._settings['delimiters']['callMacroArgs']
        regex.sub(processExtendedArgs, extendedArgString)

        
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
        
    for RE in templateObj._settings['delimiters']['callMacro']:
        templateDef = RE.sub(subber, templateDef)

    return templateDef


def preProcessRawDirectives(templateObj, templateDef):
    """extract all chunks of the template that have been escaped with the #raw
    directive"""
    def subber(match, templateObj=templateObj):
        unparsedBlock = match.group(1)
        blockID = '_' + str(id(unparsedBlock))
        templateObj._rawTextBlocks[blockID] = unparsedBlock
        return '#include raw ' + templateObj.setting('placeholderStartToken') \
               + 'rawTextBlocks.' + blockID + '/#' 
    
    if not hasattr(templateObj, '_rawTextBlocks'):
        templateObj._rawTextBlocks = {}
        
    for RE in templateObj._settings['delimiters']['rawDirective']:
        templateDef = RE.sub(subber, templateDef)
    return templateDef



def preProcessIncludeDirectives(templateObj, templateDef):
    """Replace any #include statements with their substitution value.  This
    method can handle includes from file and from placeholders such as
    $getBodyTemplate"""

    import Template                         # import it here to avoid circ. imports
    
    if not hasattr(templateObj, '_rawIncludes'):
        templateObj._rawIncludes = {}
    if not hasattr(templateObj, '_parsedIncludes'):
        templateObj._parsedIncludes = {}

    RESTART = [False,]
    def subber(match, templateObj=templateObj, RESTART=RESTART, Template=Template):
        args = match.group(1).strip()

        # do a safety/security check on this tag
        ##validateIncludeDirective(templateObj, args)
        
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
        if args.startswith( templateObj.setting('placeholderStartToken') ):
            translatedPlaceholder = templateObj.translatePlaceholderVars(args)
            includeString = templateObj.placeholderProcessor.evalPlaceholderString(
                translatedPlaceholder)
            
        elif args.startswith('"') or args.startswith("'"):
            fileName = args[1:-1]
            fileName = templateObj.normalizePath( fileName )
            includeString = templateObj.getFileContents( fileName )

        ## now process finish include
        if raw:            
            includeID = '_' + str(id(includeString))
            templateObj._rawIncludes[includeID] = includeString
            return templateObj.setting('placeholderStartToken') + \
                   '{rawIncludes.' + includeID + '}'
        elif directInclude:
            RESTART[0] = True
            return includeString
        else:
            #@@ autoUpdate behaviour needs to be implemented
            includeID = '_' + str(id(includeString))
            nestedTemplate = Template.Template(
                templateDef=includeString,
                overwriteSettings=templateObj.settings(),
                preBuiltSearchList=templateObj.searchList(),
                setVars = templateObj._setVars,
                cheetahBlocks=templateObj._cheetahBlocks,
                macros=templateObj._macros,
                )
            templateObj._parsedIncludes[includeID] = nestedTemplate
            if not hasattr(nestedTemplate, 'respond'):
                nestedTemplate.compileTemplate()
            return templateObj.setting('placeholderStartToken') + \
                   '{parsedIncludes.' + includeID + '.respond(trans, iAmNested=True)}'

    for RE in templateObj._settings['delimiters']['includeDirective']:
        templateDef = RE.sub(subber, templateDef)
        
    if RESTART[0]:
        return Template.RESTART(templateDef)
    else:
        return templateDef


def preProcessBlockDirectives(templateObj, templateDef):
    """process the block directives"""

    def handleBlock(blockName, startTagMatch, endTagRE,
                    templateDef=templateDef, templateObj=templateObj):

        endTagMatch = endTagRE.search(templateDef)
        blockContents = templateDef[startTagMatch.end() : endTagMatch.start()]

        if not templateObj._cheetahBlocks.has_key(blockName):
            templateObj._cheetahBlocks[blockName] = blockContents

        if templateObj.setting('includeBlockMarkers'):
            markerStart = templateObj._settings['blockMarkerStart']
            markerEnd = templateObj._settings['blockMarkerEnd']
        
            replaceString = markerStart[0] + blockName + markerStart[1] + \
                   '#include direct ' + templateObj.setting('placeholderStartToken') + \
                   'cheetahBlocks.' + blockName + '/#' + \
                   markerEnd[0] + blockName + markerEnd[1]
        else:
            replaceString = '#include direct ' + templateObj.setting('placeholderStartToken') + \
                            'cheetahBlocks.' + blockName + '/#'

        return templateDef[0:startTagMatch.start()] + replaceString + \
                   templateDef[endTagMatch.end():]

    ## handle the whitespace-gobbling blocks

    for startTagRE in templateObj.setting('delimiters')['blockDirectiveStart']:

        while startTagRE.search(templateDef):
            startTagMatch = startTagRE.search(templateDef)
            blockName = startTagMatch.group('blockName')
            endTagRE = re.compile(r'^[\t ]*#end block[\t ]+' + blockName +
                                  r'[\t ]*(?:\r\n|\n|\r|\Z)|'+
                                  r'#end block[\t ]+' + blockName +
                                  r'[\t ]*(?:/#|\r\n|\n|\r|\Z)',
                                  re.DOTALL | re.MULTILINE)
            templateDef = handleBlock(blockName, startTagMatch, endTagRE,
                                   templateDef=templateDef)
    
    return templateDef

## codeGenerator plugins for final filtering of the generated code ##

def addPerResponseCode(templateObj, generatedCode):
    """insert the setup code that must be executed at the beginning of each
    request.

    This code has been contributed by the tagProcessors and is stored as chunks
    in the dictionary templateObj._perResponseSetupCodeChunks"""
    
    if not hasattr(templateObj,'_perResponseSetupCodeChunks'):
        return generatedCode
    
    indent = templateObj._settings['indentationStep'] * \
             templateObj._settings['initialIndentLevel']
    perResponseSetupCode = ''
    for tagProcessor, codeChunk in templateObj._perResponseSetupCodeChunks.items():
        perResponseSetupCode += codeChunk

    def insertCode(match, perResponseSetupCode=perResponseSetupCode):
        return match.group() + perResponseSetupCode

    return re.sub(r'#setupCodeInsertMarker\n', insertCode , generatedCode)


def removeEmptyStrings(templateObj, generatedCode):
    """filter out the empty-string entries that creep in between adjacent
    tags"""
    
    generatedCode = generatedCode.replace(", '''''', ",', ')
    generatedCode = re.sub(r"\s*outputList.extend(\['''''',\])\n", '\n',
                           generatedCode)
    return generatedCode

    
## varNotFound handlers ##
def varNotFound_echo(templateObj, tag):
    return templateObj.setting('placeholderStartToken') + tag

def varNotFound_bigWarning(templateObj, tag):
    return "="*15 + "&lt;" + templateObj.setting('placeholderStartToken') \
           + tag + " could not be found&gt;" + "="*15

def varNotFound_KeyError(templateObj, tag):
    raise KeyError("no '%s' in this Template Object's Search List" % tag)
