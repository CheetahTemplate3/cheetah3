#!/usr/bin/env python
# $Id: PlaceholderProcessor.py,v 1.4 2001/07/11 21:42:11 tavis_rudd Exp $
"""Provides utilities for processing $placeholders in Cheetah templates


Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>,
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.4 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2001/07/11 21:42:11 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.4 $"[11:-2]


##################################################
## DEPENDENCIES ##

import re
import sys, string
from types import StringType
from tokenize import tokenprog

#intra-package dependencies ...
import Template
import CodeGenerator
from Components import Component
import NameMapper
from Utilities import lineNumFromPos

##################################################
## GLOBALS AND CONSTANTS ##

True = (1==1)
False = (1==0)

placeholderTagsRE = re.compile(r'(?:(?<=\A)|(?<!\\))\$(?=[A-Za-z_\*\{])')

# cacheType's for $placeholders
NO_CACHE = 0
STATIC_CACHE = 1
TIMED_REFRESH_CACHE = 2

##################################################
## FUNCTIONS ##

def matchTokenOrfail(text, pos):
    match = tokenprog.match(text, pos)
    if match is None:
        raise SyntaxError(text, pos)
    return match, match.end()

##################################################
## CLASSES ##

class SyntaxError(ValueError):
    def __init__(self, text, pos):
        self.text = text
        self.pos = pos
    def __str__(self):
        lineNum = lineNumFromPos(self.text, self.pos)
        return "unfinished expression on line %d (char %d) in: \n%s " % (
            lineNum, self.pos, self.text)
        # @@ augment this to give the line number and show a normal version of the txt

class PlaceholderProcessor(CodeGenerator.TagProcessor):
    """A class for processing $placeholders in strings."""

    def __init__(self, tagRE = placeholderTagsRE, marker='placeholderTag.',
           markerEscaped = 'placeholderTag\.',
           markerLookBehind=r'(?:(?<=placeholderTag\.)|(?<=placeholderTag\.\{))'):

        nameCharLookForward = r'(?=[A-Za-z_])'
        cachedTags = re.compile(markerLookBehind + r'\*' + nameCharLookForward)
        refreshTags = re.compile(markerLookBehind +
                                 r'\s*\*([0-9\.]+?)\*' +
                                 nameCharLookForward)

        self._tagRE = tagRE
        self._marker = marker
        self._markerEscaped = markerEscaped
        self._markerLookBehind = markerLookBehind
        self._cachedTags = cachedTags
        self._refreshTags = refreshTags
        self._nameRE = re.compile(
            marker + r'(?:CACHED\.|REFRESH_[0-9]+(?:_[0-9]+){0,1}\.){0,1}([A-Za-z_0-9\.]+)')

    def mark(self, txt):
        txt = self._tagRE.sub(self._marker, txt)
        txt = self._cachedTags.sub('CACHED.', txt)
        def refreshSubber(match):
            return 'REFRESH_' + match.group(1).replace('.','_') + '.'
        txt = self._refreshTags.sub(refreshSubber, txt)
        return txt

    def splitTxt(self, txt):
        """  """
        namechars = "abcdefghijklmnopqrstuvwxyz" \
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_";
        chunks = []
        pos = 0

        MARKER = self._marker
        MARKER_LENGTH = len(MARKER)

        while 1:
            markerPos = string.find(txt, MARKER, pos)
            if markerPos < 0:
                break
            nextchar = txt[markerPos + MARKER_LENGTH]

            if nextchar == "{":
                chunks.append((0, txt[pos:markerPos]))
                pos = markerPos + MARKER_LENGTH + 1
                level = 1
                while level:
                    match, pos = matchTokenOrfail(txt, pos)
                    tstart, tend = match.regs[3]
                    token = txt[tstart:tend]

                    if token == "{":
                        level = level+1
                    elif token == "}":
                        level = level-1
                chunks.append((1, txt[markerPos + MARKER_LENGTH + 1 : pos-1]))

            elif nextchar in namechars:
                chunks.append((0, txt[pos:markerPos]))
                match, pos = matchTokenOrfail(txt, markerPos + MARKER_LENGTH)

                while pos < len(txt):
                    if txt[pos] == "." and \
                        pos+1 < len(txt) and txt[pos+1] in namechars:

                        match, pos = matchTokenOrfail(txt, pos+1)
                    elif txt[pos] in "([":
                        pos, level = pos+1, 1
                        while level:
                            match, pos = matchTokenOrfail(txt, pos)
                            tstart, tend = match.regs[3]
                            token = txt[tstart:tend]
                            if token[0] in "([":
                                level = level+1
                            elif token[0] in ")]":
                                level = level-1
                    else:
                        break
                chunks.append((1, txt[markerPos + MARKER_LENGTH:pos]))

            else:
                raise SyntaxError(txt[pos:markerPos+MARKER_LENGTH], pos)
                ## @@ we shouldn't have gotten here

        if pos < len(txt):
            chunks.append((0, txt[pos:]))

        return chunks

    def wrapPlaceholders(self, txt, before='<Cheetah>placeholders__@__',
                         after='</Cheetah>'):
        """Evaluate and substitute the appropriate parts of the string."""
        result = []
        resAppend = result.append
        for live, chunk in self.splitTxt(txt):
            if live:
                resAppend( before + chunk + after )
            else:
                resAppend(chunk)

        return string.join(result, "")

    def preProcess(self, templateObj, templateDef):
        return self.wrapPlaceholders(self.mark(templateDef))

    def translatePlaceholderString(self, txt, searchList, templateObj,
                                   prefix='searchList', executeCallables=False):
        def translateSubber(match, prefix=prefix, searchList=searchList,
                            templateObj=templateObj,
                            executeCallables=executeCallables):
            name =  match.group(1)
            nameChunks = name.split('.')
            try:
                translated = prefix + searchList.translateName(name)
                if executeCallables and translated.find('(') == -1 \
                                    and callable(eval(translated)):
                    translated += '()'
                return translated
            except NameMapper.NotFound:
                if name in templateObj._localVarsList:
                    return name
                if templateObj and nameChunks[0] in templateObj._localVarsList:
                    name = 'valueForName(' + nameChunks[0] + ',"""' + \
                       '.'.join(nameChunks[1:]) + '""", exectuteCallables=True)'
                return name

        return self._nameRE.sub(translateSubber, txt)

    def translateRawPlaceholderString(self, txt, searchList, templateObj=None,
                                      prefix='searchList', executeCallables=False):
        return self.translatePlaceholderString(
            self.mark(txt), searchList, prefix=prefix, templateObj=templateObj,
            executeCallables=executeCallables)

    def initializeTemplateObj(self, templateObj):
        if not templateObj._codeGeneratorState.has_key('indentLevel'):
            templateObj._codeGeneratorState['indentLevel'] = \
                          templateObj._settings['initialIndentLevel']

        if not hasattr(templateObj,'_perResponseSetupCodeChunks'):
            templateObj._perResponseSetupCodeChunks = {}
        if not templateObj._perResponseSetupCodeChunks.has_key('placeholders'):
            ## setup the code to be included at the beginning of each response ##
            indent = templateObj._settings['indentationStep']
            baseInd = indent  * \
                   templateObj._settings['initialIndentLevel']

            templateObj._perResponseSetupCodeChunks['placeholders'] = \
                      baseInd + "if self._checkForCacheRefreshes:\n"\
                      + baseInd + indent + "timedRefreshCache = self._timedRefreshCache\n" \
                      + baseInd + indent + "currTime = currentTime()\n"\
                      + baseInd + indent + "self._timedRefreshList.sort()\n"\
                      + baseInd + indent + "if currTime >= self._timedRefreshList[0][0]:\n"\
                      + baseInd + indent * 2 +  " self._timedRefresh(currTime)\n"\
                      + baseInd + indent + "                                   \n" \
                      + baseInd + "nestedTemplates = self._nestedTemplatesCache\n" \
                      + baseInd + "components = self._componentsDict\n"

            ## initialize the caches, the localVarsList, and the timedRefreshList
            templateObj._timedRefreshCache = {} # caching timedRefresh vars
            templateObj._nestedTemplatesCache = {} # caching references to nested templates
            templateObj._componentsDict = {}       # you get the idea...
            templateObj._timedRefreshList = []
            templateObj._checkForCacheRefreshes = False

        if not hasattr(templateObj, '_localVarsList'):
            # may have already been set by #set or #for
            templateObj._localVarsList = ['trans', 'self']

        if not templateObj._codeGeneratorState.has_key('defaultCacheType'):
            templateObj._codeGeneratorState['defaultCacheType'] = None


    def processTag(self, templateObj, tag):

        ## find out what cacheType the tag has
        if not templateObj._codeGeneratorState['defaultCacheType'] == None:
            cacheType = templateObj._codeGeneratorState['defaultCacheType']
            if cacheType == TIMED_REFRESH_CACHE:
                cacheRefreshInterval = \
                        templateObj._codeGeneratorState['cacheRefreshInterval']
        else:
            cacheType = NO_CACHE

        nameChunks = tag.split('.')
        if nameChunks[0] == 'CACHED':
            del nameChunks[0]
            cacheType = STATIC_CACHE
        if nameChunks[0].startswith('REFRESH'):
            cacheType = TIMED_REFRESH_CACHE
            cacheRefreshInterval = float('.'.join(nameChunks[0].split('_')[1:]))
            del nameChunks[0]
        tag = '.'.join(nameChunks)
        
        ## deal with local vars from #set and #for directives
        if tag in templateObj._localVarsList:
            return self.wrapEvalTag(templateObj, 'str(' + tag + ')')

        elif nameChunks[0] in templateObj._localVarsList:
            translatedTag = 'valueForName(' + nameChunks[0] + ',"""' + \
                       '.'.join(nameChunks[1:]) + '""", exectuteCallables=True)'
            return self.wrapEvalTag(templateObj, "str(" + translatedTag + ")")


        searchList = templateObj.searchList()
        try:
            translatedTag = self.translatePlaceholderString(self._marker + tag, searchList, templateObj)
        except NameMapper.NotFound:
            return templateObj._settings['varNotFound_handler'](templateObj, tag)

        if tag.find('(') == -1:
            safeToAutoCall = True
        else:
            safeToAutoCall = False

        isCallable = False
        if safeToAutoCall:
            tagValue = eval(translatedTag)
            if isinstance(tagValue, Component):
                templateObj._componentsDict[tag] = tagValue
                return self.wrapEvalTag(templateObj, 'components["""' +
                                        tag + '"""](trans, templateObj=self)')
            elif isinstance(tagValue, Template.Template):
                templateObj._nestedTemplatesCache[tag] = tagValue.respond
                return self.wrapEvalTag(templateObj, 'nestedTemplates["""' +
                                        tag + '"""](trans, iAmNested=True)')
            elif callable(tagValue):
                isCallable = True
                tagValue = tagValue()

        if cacheType == STATIC_CACHE:
            if not safeToAutoCall:
                tagValue = eval(translatedTag)
            return str(tagValue)
        elif cacheType == TIMED_REFRESH_CACHE:
            if safeToAutoCall and isCallable:
                translatedTag = translatedTag + '()'
            templateObj._setTimedRefresh(translatedTag, cacheRefreshInterval)
            return self.wrapEvalTag(
                templateObj,
                'timedRefreshCache["""' + translatedTag + '"""]')
        else:
            # NO_CACHE or is not safe to cache
            if safeToAutoCall and isCallable:
                return self.wrapEvalTag(templateObj, "str(" + translatedTag + "())")
            else:
                return self.wrapEvalTag(templateObj, "str(" + translatedTag + ")")
