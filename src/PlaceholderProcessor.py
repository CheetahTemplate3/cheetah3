#!/usr/bin/env python
# $Id: PlaceholderProcessor.py,v 1.20 2001/08/10 18:46:22 tavis_rudd Exp $
"""Provides utilities for processing $placeholders in Cheetah templates

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>,
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.20 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2001/08/10 18:46:22 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.20 $"[11:-2]


##################################################
## DEPENDENCIES ##

import re
import sys, string
from types import StringType
from tokenize import tokenprog

#intra-package dependencies ...
from TagProcessor import TagProcessor
from Components import Component
import NameMapper
from Utilities import lineNumFromPos
#import Template                    # imported below to avoid circ. imports
##################################################
## GLOBALS AND CONSTANTS ##

True = (1==1)
False = (1==0)

# define some RE chunks for use in PlaceholderProcessor.setTagStartToken()
escCharLookBehind = r'(?:(?<=\A)|(?<!\\))'
validSecondCharsLookAhead = r'(?=[A-Za-z_\*\{])'

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

class PlaceholderProcessor(TagProcessor):
    """A class for processing $placeholders in strings."""

    def __init__(self, templateObj, tagStartToken = '$', marker=' placeholderTag.',
           markerEscaped = ' placeholderTag\.',
           markerLookBehind=r'(?:(?<= placeholderTag\.)|(?<= placeholderTag\.\{))'):
        """Setup the regexs used by this class

        All $placeholders are translated into valid Python code by swapping
        'tagStartToken' ($) for 'marker'.  This marker is then used by the
        parser (i.e. self.splitTxt()) to find the start of each placeholder and
        allows $vars in function arg lists to be parsed correctly.  '$x()'
        becomes ' placeholderTag.x()' when it's marked.

        The marker starts with a space to allow $var$var to be parsed correctly.
        $a$b is translated to --placeholderTag.a placeholderTag.b-- instead of
        --placeholderTag.aplaceholderTag.b--, which the parser would mistake for
        a single $placeholder The extra space is removed by the parser."""

        TagProcessor.__init__(self, templateObj)
        nameCharLookForward = r'(?=[A-Za-z_])'
        cachedTags = re.compile(markerLookBehind + r'\*' + nameCharLookForward)
        refreshTags = re.compile(markerLookBehind +
                                 r'\s*\*([0-9\.]+?)\*' +
                                 nameCharLookForward)

        self.setTagStartToken(tagStartToken)
        self._marker = marker
        self._markerEscaped = markerEscaped
        self._markerLookBehind = markerLookBehind
        self._cachedTags = cachedTags
        self._refreshTags = refreshTags
        self._nameRE = re.compile(
            marker + r'(?:CACHED\.|REFRESH_[0-9]+(?:_[0-9]+){0,1}\.){0,1}([A-Za-z_0-9\.]+)')

    def setTagStartToken(self, theToken):
        """Change the token used to identify the beginning of a
        placeholderTag. The default is '$'."""
        
        self._tagStartToken = theToken        
        theTokenEsc = re.sub(r'([\$\^\*\+\.\?\{\}\[\]\(\)\|\\])', r'\\\1' , theToken)
        self.setTagStartTokenRE(re.compile(escCharLookBehind +
                                           theTokenEsc +
                                           validSecondCharsLookAhead))

    def tagStartToken(self):
        return self._tagStartToken
    def setTagStartTokenRE(self, tagTokenRE):
        """Change the regular expression used to identify the beginning of a
        placeholderTag."""
        
        self._tagStartTokenRE = tagTokenRE

    def escapePlaceholders(self, theString):
        """Escape any escaped placeholders in the string."""

        return theString.replace(self._tagStartToken, '\\' + self._tagStartToken)

    def unescapePlaceholders(self, templateObj, theString):
        """Unescape any escaped placeholders in the string.
        
        This method is called by the Template._codeGenerator() in stage 1, which
        is why the first arg is 'templateObj.  self.escapePlaceholders() isn't
        called by Template._codeGenerator() so it doesn't take a templateObj arg."""

        return theString.replace('\\' + self._tagStartToken, self._tagStartToken)

    def mark(self, txt):
        """Swap the $'s for a marker that can be parsed as valid python code.
        Default is 'placeholder.'

        Also mark whether the placeholder is to be statically cached or
        timed-refresh cached"""
        
        txt = self._tagStartTokenRE.sub(self._marker, txt)
        txt = self._cachedTags.sub('CACHED.', txt)
        def refreshSubber(match):
            return 'REFRESH_' + match.group(1).replace('.','_') + '.'
        txt = self._refreshTags.sub(refreshSubber, txt)
        return txt
    
    def initializeTemplateObj(self):
        """Initialize the templateObj so that all the necessary attributes are
        in place for the tag-processing stage"""

        templateObj = self.templateObj()
        TagProcessor.initializeTemplateObj(self)
        
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

    def splitTxt(self, txt):
        
        """Split a text string containing marked placeholders
        (e.g. self.mark(txt)) into a list of plain text VS placeholders.

        This is the core of the placeholder parsing!
        """
        
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
        
        """Wrap all marked placeholders in a template definition in the internal
        Cheetah tags so that they will be picked up by the tag processor."""
        
        result = []
        resAppend = result.append
        for live, chunk in self.splitTxt(txt):
            if live:
                resAppend( before + chunk + after )
            else:
                resAppend(chunk)

        return string.join(result, "")

    def preProcess(self, templateObj, templateDef):
        """Do the preProcessing stuff for stage 1 of the Template class'
        code-generator"""
        return self.wrapPlaceholders(self.mark(templateDef))


    def translatePlaceholderString(self, txt):
        """Translate a marked placeholder string into valid Python code."""

        templateObj = self.templateObj()
        searchList = templateObj.searchList()
        def translateName(name, searchList=searchList, templateObj=templateObj):
            
            import Template                         # import it here to avoid circ. imports

            ## get rid of the 'cache-type' tokens
            # - these are handled by the tag-processor instead
            nameChunks = name.split('.')
            if nameChunks[0] == 'CACHED':
                    del nameChunks[0]
            if nameChunks[0].startswith('REFRESH'):
                del nameChunks[0]
            name = '.'.join(nameChunks)

            ## split the name into a part that NameMapper can handle and the rest
            firstSpecialChar = re.search(r'\(|\[', name)
            if firstSpecialChar:         # NameMapper can't handle [] or ()
                firstSpecialChar = firstSpecialChar.start()
                nameMapperPartOfName, remainderOfName = \
                                      name[0:firstSpecialChar], name[firstSpecialChar:]
                remainderOfName = remainderOfName
            else:
                nameMapperPartOfName = name
                remainderOfName = ''

            ## only do autocalling on names that have no () in them
            if name.find('(') == -1 and templateObj.setting('useAutocalling'):
                safeToAutoCall = True
            else:
                safeToAutoCall = False
            
            ## deal with local vars from #set and #for directives
            if name in templateObj._localVarsList:
                return name
            elif nameChunks[0] in templateObj._localVarsList:
                translatedName = 'valueForName(' + nameChunks[0] + ',"""' + \
                           '.'.join(nameChunks[1:]) + '""", executeCallables=' + \
                           str(safeToAutoCall) + ')' + remainderOfName
                return translatedName

            ## Translate the NameMapper part of the Name
            translatedName = 'searchList.get("' + \
                           nameMapperPartOfName + '", executeCallables=' + \
                           str(safeToAutoCall) + ')' + remainderOfName
            return translatedName


        ##########################
        resultList = []
        for live, chunk in self.splitTxt(txt):
            if live:
                if self._nameRE.search(chunk):
                    chunk = self.translatePlaceholderString(chunk)
                resultList.append( translateName(chunk) ) # using the function from above
            else:
                resultList.append(chunk)

        return string.join(resultList, "")
    

    def translateRawPlaceholderString(self, txt):
        """Translate raw $placeholders in a string directly into valid Python code.

        This method is used for handling $placeholders in #directives
        """

        return self.translatePlaceholderString(self.mark(txt))

        
    def processTag(self, tag):

        """This method is called by the Template class for every $placeholder
        tag in the template definition

        It is a wrapper around self.translatePlaceholderString that deals with caching"""

        templateObj = self.templateObj()
        ## find out what cacheType the tag has
        if not templateObj._codeGeneratorState['defaultCacheType'] == None:
            cacheType = templateObj._codeGeneratorState['defaultCacheType']
            if cacheType == TIMED_REFRESH_CACHE:
                cacheRefreshInterval = \
                        templateObj._codeGeneratorState['cacheRefreshInterval']
        else:
            cacheType = NO_CACHE

        ## examine the namechunks for the caching keywords
        nameChunks = tag.split('.')
        if nameChunks[0] == 'CACHED':
            del nameChunks[0]
            cacheType = STATIC_CACHE
        if nameChunks[0].startswith('REFRESH'):
            cacheType = TIMED_REFRESH_CACHE
            cacheRefreshInterval = float('.'.join(nameChunks[0].split('_')[1:]))
            del nameChunks[0]
        tag = '.'.join(nameChunks)


        ## translate the tag into Python code using self.translatePlaceholderString
        translatedTag = self.translatePlaceholderString(self._marker + tag)

        
        ## deal with the caching and return the proper code to the code-generator
        searchList = templateObj.searchList()
        if cacheType == STATIC_CACHE:
            return str(eval(translatedTag)).replace("'''",r"\'\'\'")
        elif cacheType == TIMED_REFRESH_CACHE:
            templateObj._setTimedRefresh(translatedTag, cacheRefreshInterval)
            return self.wrapEvalTag(
                'timedRefreshCache["""' + translatedTag + '"""]')
        else:
            return self.wrapEvalTag("str(" + translatedTag + ")")





