#!/usr/bin/env python
# $Id: CodeGenerator.py,v 1.2 2001/06/13 16:49:52 tavis_rudd Exp $
"""Utilities, processors and filters for Cheetah's codeGenerator

Cheetah's codeGenerator is designed to be extensible with plugin
functions.  This module contains the default plugins.

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.2 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2001/06/13 16:49:52 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.2 $"[11:-2]

##################################################
## DEPENDENCIES ##

import re
import types
from time import time as currentTime # used in the cache refresh code

# intra-package imports ...
import NameMapper
from Validators import \
     validateDisplayLogicCode, \
     validateArgStringInPlaceholderTag, \
     validateIncludeDirective, \
     validateMacroDirective, \
     validateSetDirective

from Delimeters import delimeters
from Components import Component
import Template
from Utilities import lineNumFromPos
##################################################
## CONSTANTS & GLOBALS ##

True = (1==1)
False = (0==1)


# cacheType's for $placeholders
NO_CACHE = 0
STATIC_CACHE = 1
TIMED_REFRESH_CACHE = 2

##################################################
## CLASSES ##

class Error(Exception):
    pass

class NoDefault:
    pass

##################################################
## FUNCTIONS ##

def swapDelims(string, delimStruct, newStartDelim, newEndDelim,
               unescapeEscaped=True):
    """return a copy of 'string' with the delimeters specified in delimStruct
    replaced with the newStartDelim and newEndDelim"""
    
    def replaceDelims(match, newStartDelim=newStartDelim,
                      newEndDelim=newEndDelim):
                
        return newStartDelim + match.group(1) + newEndDelim

    startDelim = delimStruct['start']
    endDelim = delimStruct['end']
    startDelimEscaped = delimStruct['startEscaped']
    endDelimEscaped = delimStruct['endEscaped']
    placeholderRE = delimStruct['placeholderRE']
    
    if startDelimEscaped:
        string = string.replace(startDelimEscaped,'<startDelimEscaped>')
    
    if endDelimEscaped:
        string = string.replace(endDelimEscaped,'<endDelimEscaped>')
        
    ## do the relacement ##
    string = placeholderRE.sub(replaceDelims, string)
        
    if startDelimEscaped:
        if unescapeEscaped:
            string = string.replace('<startDelimEscaped>', startDelim)
        else:
            string = string.replace('<startDelimEscaped>', startDelimEscaped)        
    
    if endDelimEscaped:
        if unescapeEscaped:
            string = string.replace('<endDelimEscaped>', endDelim)
        else:
            string = string.replace('<endDelimEscaped>', endDelimEscaped)

    ##
    return string

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
    
    for regex in templateObj._settings['extDelimeters']['comments']:
        templateDef = regex.sub(subber, templateDef)
        
    return templateDef

def preProcessSlurpDirective(templateObj, templateDef):
    """cut #slurp's out of the templateDef"""
    def subber(match):
        return ''
    
    for regex in templateObj._settings['extDelimeters']['slurp']:
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

    for RE in templateObj._settings['extDelimeters']['dataDirective']:
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
                
        macroBody = match.group(2)

        def handleArgsUsedInBody(match, argNamesList=argNamesList):
            """check each $var in the macroBody to see if it is in this macro's
            argNamesList and needs substituting"""
            
            if match.group(1) in argNamesList:
                return "''' + str(" + match.group(1) + ") + '''"
            else:
                return match.group()

        for delimStruct in \
            templateObj._settings['codeGenerator']['coreTags']['placeholders']['delims']:
            
            regex = delimStruct['placeholderRE']
            macroBody = regex.sub(handleArgsUsedInBody,
                                  macroBody.replace("'''","\'\'\'"))
        
        if macroName not in vars().keys():
            macroFuncName =  macroName
        else:
            macroFuncName =  'macroFunction'
            
        macroCode = "def " + macroFuncName + "(" + macroArgstring + "):\n" + \
                    "    return '''" + macroBody + "'''\n"

        exec macroCode in None, None
        exec "templateObj._macros[macroName] = " + macroFuncName in vars()
        
        return ''

    for RE in templateObj._settings['extDelimeters']['macroDirective']:
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
            macroArgstring = processPlaceholdersInString(templateObj, macroArgstring,
                                                           replaceWithValue=True,
                                                           wrapInQuotes=True)
        except NameMapper.NotFound, name:
            line = lineNumFromPos(match.string, match.start())
            raise Error('Undeclared variable $' + str(name) + \
                        ' used in macro call #'+ macroSignature + ' on line ' +
                        str(line))
        
            
        validateMacroDirective(templateObj, macroArgstring)
        if macroName in templateObj._macros.keys():
            return eval('templateObj._macros[macroName](' + macroArgstring + ')',
                        vars())
        else:
            raise Error('The macro ' + macroName + \
                        ' was called, but it does not exist')

    for RE in templateObj._settings['extDelimeters']['lazyMacroCalls']:
        templateDef = RE.sub(handleMacroCalls, templateDef)
    return templateDef


def preProcessExplicitMacroCalls(templateObj, templateDef):
    """process the explicit callMacro directives"""
    
    def subber(match, templateObj=templateObj):
        macroName = match.group('macroName').strip()
        argString = match.group('argString')
        extendedArgString = match.group('extendedArgString')

        try:
            argString = processPlaceholdersInString(templateObj, argString,
                                                      replaceWithValue=True,
                                                      wrapInQuotes=True)
        except NameMapper.NotFound, name:
            line = lineNumFromPos(match.string, match.start())
            raise Error('Undeclared variable $' + str(name) + 
                        ' used in macro call #'+ macroSignature + 
                        ' on line ' + str(line))

        extendedArgsDict = {}
        
        def processExtendedArgs(match, extendedArgsDict=extendedArgsDict):
            """check each $var in the macroBody to see if it is in this macro's
            argNamesList and needs substituting"""
            extendedArgsDict[ match.group('argName') ] = match.group('argValue')
            return ''

        regex = templateObj._settings['extDelimeters']['callMacroArgs']
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
        
    for RE in templateObj._settings['extDelimeters']['callMacro']:
        templateDef = RE.sub(subber, templateDef)

    return templateDef


def preProcessRawDirectives(templateObj, templateDef):
    """extract all chunks of the template that have been escaped with the #raw
    directive"""
    def subber(match, templateObj=templateObj):
        unparsedBlock = match.group(1)
        blockID = str(id(unparsedBlock))
        templateObj._unparsedBlocks[blockID]= unparsedBlock
        return '<CheetahUnparsedBlock>' + blockID + \
               '</CheetahUnparsedBlock>'
    
    if not hasattr(templateObj, '_unparsedBlocks'):
        templateObj._unparsedBlocks = {}
        
    for RE in templateObj._settings['extDelimeters']['rawDirective']:
        templateDef = RE.sub(subber, templateDef)
    return templateDef

def postProcessRawDirectives(templateObj, templateDef):
    """reinsert all chunks that were removed in the preProcessing stage by the
    #raw directive"""
    
    def subber(match, templateObj=templateObj):
        blockID = match.group(1)
        return templateObj._unparsedBlocks[blockID]

    templateDef = re.sub(r'<CheetahUnparsedBlock>(.+)' +
                      r'</CheetahUnparsedBlock>',
                      subber, templateDef)
    return templateDef


def preProcessIncludeDirectives(templateObj, templateDef, RE):
    """replace any #include statements with their substitution value.  This method
    can handle includes from file (absolute paths only at the moment) and from
    placeholders such as $getBodyTemplate"""
    
    def subber(match, templateObj=templateObj):
        args = match.group(1).strip()
        # do a safety/security check on this tag
        validateIncludeDirective(templateObj, args)
        includeString = match.group(1).strip()        
        
        if args.split()[0] == 'raw':
            return '<CheetahRawInclude>' + \
                   re.sub(r'(?:(?<=\A)|(?<!\\))\$',r'\$', 
                          ' '.join(args.split()[1:] ) ) + \
                          '</CheetahRawInclude>'
        else:
        
            if args[0] == '$':
                # it's a placeholder, substitute its value
                if args.find('${') == -1:  # it's a single $placeholder tag
                    includeString = templateObj.mapName(args[1:],
                                                        executeCallables=True)
                else:  # it's a ${...} placeholder tag
                    includeString = templateObj.mapName(parseArgs[2:-1],
                                                        executeCallables=True)
                    
            elif args.startswith('"') or args.startswith("'"):
                fileName = args[1:-1]
                includeString = templateObj.getFileContents( fileName )
                
            return includeString

    templateDef = RE.sub(subber, templateDef)
    return templateDef

def preProcessBlockDirectives(templateObj, templateDef):
    """process the block directives"""
    if not hasattr(templateObj, '_blocks'):
        templateObj._blocks = {}

    def handleBlock(blockName, startTagMatch, endTagRE,
                    templateDef=templateDef, templateObj=templateObj):

        endTagMatch = endTagRE.search(templateDef)
        blockContents = templateDef[startTagMatch.end() : endTagMatch.start()]

        if not hasattr(templateObj, '_blocks'):
            templateObj._blocks = {}

        if not templateObj._blocks.has_key(blockName):
            templateObj._blocks[blockName] = blockContents

        if templateObj._settings['includeBlockMarkers']:
            markerStart = templateObj._settings['blockMarkerStart']
            markerEnd = templateObj._settings['blockMarkerEnd']
        
            replaceString = markerStart[0] + blockName + markerStart[1] + \
                   '#parse $blocks.' + blockName + '/#' + \
                   markerEnd[0] + blockName + markerEnd[1]
        else:
            replaceString = '#include $blocks.' + blockName + '/#'

        return templateDef[0:startTagMatch.start()] + replaceString + \
                   templateDef[endTagMatch.end():]

    ## handle the whitespace-gobbling blocks

    for startTagRE in templateObj._settings['extDelimeters']['blockDirectiveStart']:

        while startTagRE.search(templateDef):
            startTagMatch = startTagRE.search(templateDef)
            blockName = startTagMatch.group('blockName')
            endTagRE = re.compile(r'^[\t ]*#end block[\t ]+' + blockName +
                                  r'[\t ]*(?:\r\n|\n|\Z)|'+
                                  r'#end block[\t ]+' + blockName +
                                  r'[\t ]*(?:/#|\r\n|\n|\Z)',
                                  re.DOTALL | re.MULTILINE)
            templateDef = handleBlock(blockName, startTagMatch, endTagRE,
                                   templateDef=templateDef)
    
    return templateDef


def preProcessSetDirectives(templateObj, templateDef):
    """escape $vars in the directives, so the placeholderTagProcessor doesn't
    picked them up"""
    
    def subber(match):
        directive = match.group()
        return re.sub(r'(?:(?<=\A)|(?<!\\))\$',r'\$',match.group())

    for delimStruct in \
        templateObj._settings['codeGenerator']['coreTags']['setDirective']['delims']:
        
        regex = delimStruct['placeholderRE']
        templateDef = regex.sub(subber, templateDef)

    return templateDef

def postProcessRawIncludeDirectives(templateObj, templateDef):
    """replace any include statements with their substitution value.  This
    method can handle includes from file (absolute paths only at the moment) and
    from $placeholders such as $getBodyTemplate"""
    
    def subber(match, templateObj=templateObj):
        args = match.group(1).strip()
        # do a safety/security check on this tag
        validateIncludeDirective(templateObj, args)
        
        includeString = match.group(1).strip()
        
        if args[0] == '$':
            # it's a $placeholder tag, substitute its value
            if args.find('${') == -1:
                # it's a single $placeholder tag
                includeString = templateObj.mapName(args[1:],
                                                    executeCallables=True)
            else:  # it's a ${...} placeholder tag
                includeString = templateObj.mapName(args[2:-1],
                                                    executeCallables=True)
        elif args.startswith('"') or args.startswith("'"):
            fileName = args[1:-1]
            includeString = templateObj.getFileContents( fileName )
            
        return  includeString

    templateDef = re.sub(r'<CheetahRawInclude>(.+)' +
                      r'</CheetahRawInclude>',
                      subber, templateDef)
    return templateDef


def preProcessDisplayLogic(templateObj, templateDef):
    """swap $ for \$ in the displayLogic, so the placeholderTagProcessor doesn't
    picked them up"""
    
    def subber(match):
        return re.sub(r'(?:(?<=\A)|(?<!\\))\$',r'\$',match.group())
    
    for delim in \
        templateObj._settings['codeGenerator']['coreTags']['displayLogic']['delims']:
        
        templateDef = delim['placeholderRE'].sub(subber, templateDef)

    return templateDef


## codeGenerator plugins for processing each of the token-prefixed tags ##

def cacheDirectiveStartTagProcessor(templateObj, directive):
    if not templateObj._codeGeneratorState.has_key('defaultCacheType'):
        templateObj._codeGeneratorState['defaultCacheType'] = NoDefault

    directive = directive.strip()
    
    if not directive:
        templateObj._codeGeneratorState['defaultCacheType'] = STATIC_CACHE
    else:
        templateObj._codeGeneratorState['defaultCacheType'] = TIMED_REFRESH_CACHE
        templateObj._codeGeneratorState['cacheRefreshInterval'] = float(directive)
    return "''"

def cacheDirectiveEndTagProcessor(templateObj, directive):
    templateObj._codeGeneratorState['defaultCacheType'] = NoDefault
    return "''"

def setDirectiveTagProcessor(templateObj, directive):
    """generate python code from setDirective tags, and register the vars with
    placeholderTagProcessor as local vars."""
    validateSetDirective(templateObj, directive)
    
    firstEqualSign = directive.find('=')
    varName = directive[0: firstEqualSign].replace('$','').strip()
    valueString = directive[firstEqualSign+1:]
    valueString = processPlaceholdersInString(templateObj, valueString)
    templateObj._localVarsList.append(varName)

    indent = templateObj._settings['codeGenerator']['indentationStep']
    if not templateObj._codeGeneratorState.has_key('indentLevel'):
        templateObj._codeGeneratorState['indentLevel'] = \
                    templateObj._settings['codeGenerator']['initialIndentLevel']

    return indent*(templateObj._codeGeneratorState['indentLevel']) + varName + \
           "=" + valueString + "\n" + \
           indent * templateObj._codeGeneratorState['indentLevel']

def placeholderTagProcessor(templateObj, tag, convertToString=True,
                            cacheType=NoDefault, cacheRefreshInterval=15):
    """generate the python code that will be evaluated for $placeholder
    during each request.

    This implementation handles caching of $placeholders and will auto-detect
    'components', nested templates, and vars that have been set locally in for
    loops or with the #set directive."""

    ## setup a reference to templateObj so $placeholders in argstrings can be eval'd here
    self = templateObj

    ## do the rest of the setup
    if not hasattr(templateObj,'_perResponseSetupCodeChunks'):
        templateObj._perResponseSetupCodeChunks = {}    
    if not templateObj._perResponseSetupCodeChunks.has_key('placeholders'):
        ## setup the code to be included at the beginning of each response ##
        indent = templateObj._settings['codeGenerator']['indentationStep']  * \
                 templateObj._settings['codeGenerator']['initialIndentLevel']
        
        templateObj._perResponseSetupCodeChunks['placeholders'] = \
                  indent + "if self._checkForCacheRefreshes:\n"\
                  + indent * 2 + "currTime = currentTime()\n"\
                  + indent * 2 + "self._timedRefreshList.sort()\n"\
                  + indent * 2 + "if currTime >= self._timedRefreshList[0][1]:\n"\
                  + indent * 3 +  " self._timedRefresh(currTime)\n"\
                  + indent + "                                   \n" \
                  + indent + "timedRefreshCache = self._timedRefreshCache\n" \
                  + indent + "callableNames = self._callableNamesCache\n" \
                  + indent + "nestedTemplates = self._nestedTemplatesCache\n" \
                  + indent + "components = self._componentsDict\n"

        ## initialize the caches, the localVarsList, and the timedRefreshList
        templateObj._timedRefreshCache = {} # caching timedRefresh vars
        templateObj._callableNamesCache = {} # caching name mappings that are callable
        templateObj._nestedTemplatesCache = {} # caching references to nested templates
        templateObj._componentsDict = {}         # you get the idea...
        templateObj._timedRefreshList = []
        templateObj._checkForCacheRefreshes = False
        if not hasattr(templateObj, '_localVarsList'):
            # may have already been set by #set or #for
            templateObj._localVarsList = []

    if not templateObj._codeGeneratorState.has_key('defaultCacheType'):
        templateObj._codeGeneratorState['defaultCacheType'] = NoDefault

    ## Check for an argString in the tag ##
    firstParenthesis = tag.find('(')
    if firstParenthesis != -1:
        argString = tag[firstParenthesis+1:-1]
        
        #@@ disabled for the time-being
        #argString = processPlaceholdersInString(templateObj, argString)
        validateArgStringInPlaceholderTag(templateObj, argString)
        varName = tag[0:firstParenthesis]
    else:
        varName = tag
        argString = ''

    ## check for caching of the $placeholder ##
    if cacheType == NoDefault:
        if not templateObj._codeGeneratorState['defaultCacheType'] == NoDefault:
            cacheType = templateObj._codeGeneratorState['defaultCacheType']
            if cacheType == TIMED_REFRESH_CACHE:
                cacheRefreshInterval = \
                        templateObj._codeGeneratorState['cacheRefreshInterval']
        else:
            cacheType = NO_CACHE

    if varName.find('*') != -1:
        if re.match(r'\*[A-Za-z_]',varName.strip()):
            # it's a static cached $placeholder
            cacheType = STATIC_CACHE
            varName = (varName.split('*'))[1]
        else:
            # timedRefresh dynamic var: $*interval*varName -> $*15*var
            cacheType = TIMED_REFRESH_CACHE
            cacheRefreshInterval, varName = varName[1:].split('*')
            cacheRefreshInterval = float(cacheRefreshInterval)
            
    if cacheType == TIMED_REFRESH_CACHE:
        templateObj._setTimedRefresh(varName, cacheRefreshInterval)

    ##deal with local vars from #set and #for directives
    splitVarName = varName.split('.')
    if varName in templateObj._localVarsList:
        if argString:
            processedTag = varName + '(' + argString + ')'
        else:
            processedTag = varName
        if convertToString:
            processedTag = 'str(' + processedTag + ')'
        return processedTag

    elif splitVarName[0] in templateObj._localVarsList:
        if argString:
            processedTag = 'valueForName(' + splitVarName[0] + ',"""' + \
                           '.'.join(splitVarName[1:]) + '""")(' + argString + ')'
        else:
            processedTag = 'valueForName(' + splitVarName[0] + ',"""' + \
                           '.'.join(splitVarName[1:]) + '""", exectuteCallables=True)'
        if convertToString:
            processedTag = 'str(' + processedTag + ')'
        return processedTag

    
    ## find a value for the $placeholder
    try:
        binding = templateObj.mapName(varName)
    except NameMapper.NotFound:
        return templateObj._settings['varNotFound_handler'](templateObj, tag)


    ## generate the Python code that will evaluate to the value of the placeholder
    
    if isinstance(binding, Component):
        templateObj._componentsDict[varName] = binding
        processedTag = 'components["' + varName + '"](trans, templateObj=self)'

    elif (type(binding) == types.MethodType and isinstance(binding.im_self,
                                                           Component)):
        # it's a method of a component
        templateObj._componentsDict[varName] = binding
        processedTag = 'components["' + varName + '"](trans, templateObj=self)'
    
    elif isinstance(binding, Template.Template):
        templateObj._nestedTemplatesCache[varName] = binding.__str__
        processedTag = 'nestedTemplates["' + varName + '"](trans, iAmNested=True)'

    elif cacheType == STATIC_CACHE:
        if callable(binding):
            if argString:
                value = "'''" + str(eval('binding(' + argString + \
                                         ')')).replace("'''",r"\'\'\'") + "'''"
            else:
                value = "'''" + str(binding()).replace("'''",r"\'\'\'") + "'''"
        else:
            value = "'''" + str(binding).replace("'''",r"\'\'\'") + "'''"
        processedTag =  value
        
    elif cacheType == TIMED_REFRESH_CACHE:
        if callable(binding):
            if argString:
                varName = varName + '(' + argString + ')'
                binding = templateObj._timedRefreshCache[varName] = \
                          str(eval('binding(' + argString + ')'))
            else:
                binding = templateObj._timedRefreshCache[varName] = str(binding())
        else:
            templateObj._timedRefreshCache[varName] = str(binding)
            
        processedTag =  'timedRefreshCache["""' + varName + '"""]'

    elif callable(binding):
        templateObj._callableNamesCache[varName] = binding
        if argString:
            processedTag = 'str(callableNames["' + varName + '"](' + \
                           argString + '))'
        else:
            if (not type(binding()) == types.StringType) and convertToString:
                processedTag = 'str(callableNames["' + varName + '"]())'
            else:
                processedTag = 'callableNames["' + varName + '"]()'
                
    else:
        if (not type(binding) == types.StringType) and convertToString:
            processedTag ='str( self.mapName("' + varName + '") )'
        else:
            processedTag ='self.mapName("' + varName + '")'
    ##
    return processedTag
    

def displayLogicTagProcessor(templateObj, displayLogic):
    """process display logic embedded in the template"""

    settings = templateObj._settings
    indent = settings['codeGenerator']['indentationStep']
    
    displayLogic = displayLogic.strip()
    validateDisplayLogicCode(templateObj, displayLogic) 

    if not hasattr(templateObj, '_localVarsList'):
        # may have already been set by #set or #for
        templateObj._localVarsList = []

    if not templateObj._codeGeneratorState.has_key('indentLevel'):
        templateObj._codeGeneratorState['indentLevel'] = \
                       settings['codeGenerator']['initialIndentLevel']

    if displayLogic.lower() in \
       settings['codeGenerator']['displayLogicblockEndings']:
        
        templateObj._codeGeneratorState['indentLevel'] -= 1
        outputCode = indent*templateObj._codeGeneratorState['indentLevel']

    elif displayLogic.lower()[0:4] in ('else','elif'):
        displayLogic = displayLogic.replace('else if','elif')
        
        if displayLogic.lower()[0:4] == 'elif':
            displayLogic = processPlaceholdersInString(templateObj, displayLogic)
        
        outputCode = indent*(templateObj._codeGeneratorState['indentLevel']-1) + \
                     displayLogic +":\n" + \
                     indent*templateObj._codeGeneratorState['indentLevel']

    elif re.match(r'if +|for +', displayLogic): # it's the start of a new block
        templateObj._codeGeneratorState['indentLevel'] += 1
        
        if displayLogic[0:3] == 'for':
            ##translate this #for $i in $list/# to this #for i in $list/#
            INkeywordPos = displayLogic.find(' in ')
            displayLogic = displayLogic[0:INkeywordPos].replace('$','') + \
                           displayLogic[INkeywordPos:]

            ## register the local vars in the loop with the templateObj  ##
            #  so placeholderTagProcessor will recognize them
            #  and handle their use appropriately
            localVars, restOfForStatement = displayLogic[3:].split(' in ')
            localVarsList =  [localVar.strip() for localVar in
                              localVars.split(',')]
            templateObj._localVarsList += localVarsList 

        displayLogic = processPlaceholdersInString(templateObj, displayLogic)
        outputCode = indent*(templateObj._codeGeneratorState['indentLevel']-1) + \
                     displayLogic + ":\n" + \
                     indent*templateObj._codeGeneratorState['indentLevel']
    
    else:                           # it's a chunk of plain python code              
        outputCode = indent*(templateObj._codeGeneratorState['indentLevel']) + \
                     displayLogic + \
                     "\n" + indent*templateObj._codeGeneratorState['indentLevel']            
        
    return outputCode

def processPlaceholdersInString(templateObj, string, replaceWithValue=False,
                                  wrapInQuotes=False):
    """search string for placeholders and return the python code needed to
    access those placeholders, or the value of the placeholders if
    replaceWithValue==True"""

    def subber(match, templateObj=templateObj, replaceWithValue=replaceWithValue,
               wrapInQuotes=wrapInQuotes):
        
        if replaceWithValue:
            if wrapInQuotes:
                return '"""' + str(
                    templateObj.mapName(match.group(1),
                                        executeCallables=True)
                    ) + '"""'
            else:
                return templateObj.mapName(match.group(1),
                                           executeCallables=True)
        else:
            return placeholderTagProcessor(templateObj, match.group(1),
                                          convertToString=False,
                                           cacheType=NO_CACHE)
        
    for delimStruct in \
        templateObj._settings['codeGenerator']['coreTags']['placeholders']['delims']:
        
        string = delimStruct['placeholderRE'].sub(subber, string)

    return string


## codeGenerator plugins for final filtering of the generated code ##

def addPerResponseCode(templateObj, generatedCode):
    """insert the setup code that must be executed at the beginning of each
    request.

    This code has been contributed by the tagProcessors and is stored as chunks
    in the dictionary templateObj._perResponseSetupCodeChunks"""
    
    if not hasattr(templateObj,'_perResponseSetupCodeChunks'):
        return generatedCode
    
    indent = templateObj._settings['codeGenerator']['indentationStep'] * \
             templateObj._settings['codeGenerator']['initialIndentLevel']
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
    generatedCode = generatedCode.replace("''', '''",'')
    generatedCode = re.sub(r"\s*outputList \+= \['''''',\]\n", '\n',
                           generatedCode)
    return generatedCode

    
## varNotFound handlers ##
def varNotFound_echo(templateObj, tag):
    return "'''$" + tag + "'''"

def varNotFound_bigWarning(templateObj, tag):
    return "'''" + "="*15 + "&lt;$" + tag + " could not be found&gt;" + \
           "="*15 + "'''"
