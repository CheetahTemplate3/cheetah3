#!/usr/bin/env python
# $Id: CodeGenerator.py,v 1.19 2001/08/04 00:09:25 tavis_rudd Exp $
"""Utilities, processors and filters for Cheetah's codeGenerator

Cheetah's codeGenerator is designed to be extensible with plugin
functions.  This module contains the default plugins.

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.19 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2001/08/04 00:09:25 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.19 $"[11:-2]

##################################################
## DEPENDENCIES ##

import re
import types
from time import time as currentTime # used in the cache refresh code

# intra-package imports ...
import TagProcessor
import NameMapper
from Validators import \
     validateDisplayLogicCode, \
     validateArgStringInPlaceholderTag, \
     validateIncludeDirective, \
     validateMacroDirective, \
     validateSetDirective

from Delimiters import delimiters
from Components import Component
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

class DisplayLogicProcessor(TagProcessor.TagProcessor):
    """A class for processing display logic tags in Cheetah Templates."""
    
    def __init__(self):
        self._tagType = TagProcessor.EXEC_TAG_TYPE
        self._delimRegexs = [delimiters['displayLogic_gobbleWS'],
                             delimiters['displayLogic']]
        self._token = 'displayLogic'
                    
    def translateTag(self, templateObj, tag):
        """process display logic embedded in the template"""
    
        settings = templateObj._settings
        indent = settings['indentationStep']
        
        tag = tag.strip()
        validateDisplayLogicCode(templateObj, tag) 
        
        if tag in ('end if','end for'):
            templateObj._codeGeneratorState['indentLevel'] -= 1
            outputCode = indent*templateObj._codeGeneratorState['indentLevel']

        elif tag in ('continue','break'):
            outputCode = indent*templateObj._codeGeneratorState['indentLevel'] + tag \
                         + "\n" + \
                         indent*templateObj._codeGeneratorState['indentLevel']
        elif tag[0:4] in ('else','elif'):
            tag = tag.replace('else if','elif')
            
            if tag[0:4] == 'elif':
                tag = templateObj.translatePlaceholderVars(tag, executeCallables=True)
                tag = tag.replace('()() ','() ') # get rid of accidental double calls
            
            outputCode = indent*(templateObj._codeGeneratorState['indentLevel']-1) + \
                         tag +":\n" + \
                         indent*templateObj._codeGeneratorState['indentLevel']
    
        elif re.match(r'if +|for +', tag): # it's the start of a new block
            templateObj._codeGeneratorState['indentLevel'] += 1
            
            if tag[0:3] == 'for':
                ##translate this #for $i in $list/# to this #for i in $list/#
                INkeywordPos = tag.find(' in ')
                tag = tag[0:INkeywordPos].replace(
                    templateObj.setting('placeholderStartToken'),'') + \
                               tag[INkeywordPos:]
    
                ## register the local vars in the loop with the templateObj  ##
                #  so placeholderTagProcessor will recognize them
                #  and handle their use appropriately
                localVars, restOfForStatement = tag[3:].split(' in ')
                localVarsList =  [localVar.strip() for localVar in
                                  localVars.split(',')]
                templateObj._localVarsList += localVarsList 
    
            tag = templateObj.translatePlaceholderVars(tag, executeCallables=True)
            tag = tag.replace('()() ','() ') # get rid of accidental double calls
            outputCode = indent*(templateObj._codeGeneratorState['indentLevel']-1) + \
                         tag + ":\n" + \
                         indent*templateObj._codeGeneratorState['indentLevel']
        
        else:                           # it's a chunk of plain python code              
            outputCode = indent*(templateObj._codeGeneratorState['indentLevel']) + \
                         tag + \
                         "\n" + indent*templateObj._codeGeneratorState['indentLevel']            
            
        return outputCode

class SetDirectiveProcessor(TagProcessor.TagProcessor):
    """A class for processing display logic tags in Cheetah Templates."""
    
    _token = 'setDirective'
    _tagType = TagProcessor.EXEC_TAG_TYPE
    _delimRegexs = [delimiters['setDirective'],]
                    
    def translateTag(self, templateObj, tag):
        """generate python code from setDirective tags, and register the vars with
        placeholderTagProcessor as local vars."""
        validateSetDirective(templateObj, tag)
        
        firstEqualSign = tag.find('=')
        varName = tag[0: firstEqualSign].replace(
            templateObj.setting('placeholderStartToken'),'').strip()
        valueString = tag[firstEqualSign+1:]
        valueString = templateObj.translatePlaceholderVars(valueString,
                                                           executeCallables=True)
        # get rid of accidental double calls
        valueString = valueString.replace('()()','()')
        
        templateObj._localVarsList.append(varName)
    
        indent = templateObj._settings['indentationStep']
        if not templateObj._codeGeneratorState.has_key('indentLevel'):
            templateObj._codeGeneratorState['indentLevel'] = \
                        templateObj._settings['initialIndentLevel']
    
        return indent*(templateObj._codeGeneratorState['indentLevel']) + varName + \
               "=" + valueString + "\n" + \
               indent * templateObj._codeGeneratorState['indentLevel']
        

class CacheDirectiveProcessor(TagProcessor.TagProcessor):
    _tagType = TagProcessor.EMPTY_TAG_TYPE
    _token = 'cacheDirective'
    _delimRegexs = [delimiters['cacheDirectiveStartTag'],]    

    def translateTag(self, templateObj, tag):
        tag = tag.strip()
        if not tag:
            templateObj._codeGeneratorState['defaultCacheType'] = \
                                       STATIC_CACHE
        else:
            templateObj._codeGeneratorState['defaultCacheType'] = \
                                       TIMED_REFRESH_CACHE
            templateObj._codeGeneratorState['cacheRefreshInterval'] = float(tag)

        
class EndCacheDirectiveProcessor(CacheDirectiveProcessor):
    _token = 'endCacheDirective'
    _delimRegexs = [delimiters['cacheDirectiveEndTag'],]    
    
    def translateTag(self, templateObj, tag):
        templateObj._codeGeneratorState['defaultCacheType'] = NoDefault


##################################################
## FUNCTIONS ##
def separateTagsFromText(initialText, placeholderRE):
    """breaks a string up into a textVsTagsList where the odd items are plain
    text and the even items are the contents of the tags matched by
    placeholderRE"""
    
    textVsTagsList = []
    position = [0,]
    
    def subber(match, textVsTagsList=textVsTagsList,
               position=position, initialText=initialText):

        textVsTagsList.append( initialText[position[0]:match.start()] )
        position[0] = match.end()
        textVsTagsList.append(match.group(1))
        return ''                       # dummy output that is ignored
        
    placeholderRE.sub(subber, initialText)  # ignoring the return value
    textVsTagsList.append(initialText[position[0]:])
    return textVsTagsList

def processTextVsTagsList(textVsTagsList, tagProcessorFunction):
    """loops through textVsTagsList - the output from separateTagsFromText() -
    and filters all the tag items with the tagProcessorFunction"""
    
    ## odd items are plain text, even ones are tags
    processedList = textVsTagsList[:]
    for i in range(1, len(processedList), 2):
        processedList[i] = tagProcessorFunction(processedList[i])
    return processedList

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
        if not 'overwrite' in args:
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
        validateMacroDirective(templateObj, macroSignature)
        
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
            else:
                return templateObj.setting('placeholderStartToken') + \
                       '{' + match.group(1) + '}'

        processor = templateObj.placeholderProcessor
        macroBody = processor.wrapPlaceholders(
            processor.mark(macroBody), before='<argInBody>', after='</argInBody>')
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

        try:
            searchList = templateObj.searchList()
            macroArgstring = templateObj.translatePlaceholderVars(macroArgstring)
            
        except NameMapper.NotFound, name:
            line = lineNumFromPos(match.string, match.start())
            raise Error('Undeclared variable ' + str(name) + \
                        ' used in macro call #'+ macroSignature + ' on line ' +
                        str(line))       
            
        validateMacroDirective(templateObj, macroArgstring)
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
            argString = templateObj.translatePlaceholderVars(argString,
                                                             executeCallables=True)
            
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
        
        validateMacroDirective(templateObj, fullArgString)
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
    """replace any #include statements with their substitution value.  This method
    can handle includes from file (absolute paths only at the moment) and from
    placeholders such as $getBodyTemplate"""

    import Template                         # import it here to avoid circ. imports
    
    if not hasattr(templateObj, '_rawIncludes'):
        templateObj._rawIncludes = {}
    if not hasattr(templateObj, '_parsedIncludes'):
        templateObj._parsedIncludes = {}

    RESTART = [False,]
    def subber(match, templateObj=templateObj, RESTART=RESTART, Template=Template):
        args = match.group(1).strip()
        # do a safety/security check on this tag
        validateIncludeDirective(templateObj, args)
        includeString = match.group(1).strip()        
        raw = False
        autoUpdate = False #True
        #@@ autoUpdate behaviour needs to be implemented
        
        if args.split()[0] == 'raw':
            raw = True
            args= ' '.join(args.split()[1:])

        if args[0] == templateObj.setting('placeholderStartToken'):
            searchList = templateObj.searchList()
            translatedArgs = templateObj.translatePlaceholderVars(args)
            includeString = eval( translatedArgs )
            
        elif args.startswith('"') or args.startswith("'"):
            fileName = args[1:-1]
            fileName = templateObj.normalizePath( fileName )
            includeString = templateObj.getFileContents( fileName )

        if raw:            
            includeID = '_' + str(id(includeString))
            templateObj._rawIncludes[includeID] = includeString
            return templateObj.setting('placeholderStartToken') + \
                   '{rawIncludes.' + includeID + '}'
        elif autoUpdate:
            includeID = '_' + str(id(includeString))
            nestedTemplate = Template.Template(
                templateDef=includeString,
                overwriteSettings=templateObj.settings(),
                searchList=templateObj.searchList(),
                cheetahBlocks=templateObj._cheetahBlocks,
                macros=templateObj._macros)
            templateObj._parsedIncludes[includeID] = nestedTemplate
            if not hasattr(nestedTemplate, 'respond'):
                nestedTemplate.startServer()
            return templateObj.setting('placeholderStartToken') + \
                   '{parsedIncludes.' + includeID + '}'
        else:
            RESTART[0] = True
            return includeString

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

        if templateObj._settings['includeBlockMarkers']:
            markerStart = templateObj._settings['blockMarkerStart']
            markerEnd = templateObj._settings['blockMarkerEnd']
        
            replaceString = markerStart[0] + blockName + markerStart[1] + \
                   '#include ' + templateObj.setting('placeholderStartToken') + \
                   'cheetahBlocks.' + blockName + '/#' + \
                   markerEnd[0] + blockName + markerEnd[1]
        else:
            replaceString = '#include ' + templateObj.setting('placeholderStartToken') + \
                            'cheetahBlocks.' + blockName + '/#'

        return templateDef[0:startTagMatch.start()] + replaceString + \
                   templateDef[endTagMatch.end():]

    ## handle the whitespace-gobbling blocks

    for startTagRE in templateObj._settings['delimiters']['blockDirectiveStart']:

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
