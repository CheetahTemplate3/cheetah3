#!/usr/bin/env python
# $Id: Parser.py,v 1.1 2001/08/10 22:41:10 tavis_rudd Exp $
"""Parser base-class for Cheetah's Template class and TagProcessor class

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.1 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/08/10 22:41:10 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.1 $"[11:-2]

##################################################
## DEPENDENCIES ##

import re
from types import StringType
from tokenize import tokenprog

# intra-package imports ...
from Utilities import lineNumFromPos, escapeRegexChars

##################################################
## CONSTANTS & GLOBALS ##

True = (1==1)
False = (0==1)

#Regex chunks for the parser
escCharLookBehind = r'(?:(?<=\A)|(?<!\\))'
validSecondCharsLookAhead = r'(?=[A-Za-z_\*\{])'
nameCharLookAhead = r'(?=[A-Za-z_])'

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

class Error(Exception):
    pass

class Parser:   
    def __init__(self, templateObj):
        """Setup some internal references to the templateObj. This method must
        be called by subclasses."""

        self._templateObj = templateObj
        ## setup some method mappings for convenience
        self.state = templateObj._getCodeGeneratorState
        self.settings = templateObj.settings
        self.setting = templateObj.setting
        self.searchList = templateObj.searchList
        self.evalPlaceholderString = templateObj.evalPlaceholderString

        self._placeholderREs = templateObj._placeholderREs
        # don't use the RE's yet as they haven't been created.
        

    ## data access methods  ##
        
    def templateObj(self):
        """Return a reference to the templateObj that controls this processor"""
        return self._templateObj

    ## generic parsing methods ##
    
    def splitExprFromTxt(self, txt, MARKER):

        """Split a text string containing marked placeholders
        (e.g. self.mark(txt)) into a list of plain text VS placeholders.

        This is the core of the placeholder parsing!
        """
        
        namechars = "abcdefghijklmnopqrstuvwxyz" \
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_";
        chunks = []
        pos = 0

        MARKER_LENGTH = len(MARKER)

        while 1:
            markerPos = txt.find(MARKER, pos)
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

    def wrapExressionsInStr(self, txt, marker, before, after):
        
        """Wrap all marked expressions in a string with the strings 'before' and
        'after'."""
        
        result = []
        resAppend = result.append
        for live, chunk in self.splitExprFromTxt(txt, marker):
            if live:
                resAppend( before + chunk + after )
            else:
                resAppend(chunk)

        return ''.join(result)


    ## placeholder-specific parsing methods ##

    def markPlaceholders(self, txt):
        """Swap the $'s for a marker that can be parsed as valid python code.
        Default is 'placeholder.'

        Also mark whether the placeholder is to be statically cached or
        timed-refresh cached"""
        REs = self._placeholderREs
        
        txt = REs['startToken'].sub(
            self.setting('placeholderMarker'), txt)
        txt = REs['cachedTags'].sub('CACHED.', txt)
        def refreshSubber(match):
            return 'REFRESH_' + match.group(1).replace('.','_') + '.'
        txt = REs['refreshTag'].sub(refreshSubber, txt)
        return txt


    def translateRawPlaceholderString(self, txt):
        """Translate raw $placeholders in a string directly into valid Python code.

        This method is used for handling $placeholders in #directives
        """
        return self.translatePlaceholderString(self.markPlaceholders(txt))


    def translatePlaceholderString(self, txt):
        """Translate a marked placeholder string into valid Python code."""

        templateObj = self.templateObj()
        searchList = templateObj.searchList()
        
        def translateName(name, templateObj=templateObj):
            
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
            translatedName = 'searchList_getMeth("' + \
                           nameMapperPartOfName + '", executeCallables=' + \
                           str(safeToAutoCall) + ')' + remainderOfName
            return translatedName

        ##########################
        resultList = []
        for live, chunk in self.splitExprFromTxt(txt, self.setting('placeholderMarker')):
            if live:
                if self._placeholderREs['nameMapperChunk'].search(chunk):
                    chunk = self.translatePlaceholderString(chunk)
                resultList.append( translateName(chunk) ) # using the function from above
            else:
                resultList.append(chunk)

        return ''.join(resultList)
    

    def escapePlaceholders(self, theString):
        """Escape any escaped placeholders in the string."""

        token = self.setting('placeholderStartToken')
        return theString.replace(token, '\\' + token)

    def unescapePlaceholders(self, templateObj, theString):
        """Unescape any escaped placeholders in the string.
        
        This method is called by the Template._codeGenerator() in stage 1, which
        is why the first arg is 'templateObj.  self.escapePlaceholders() isn't
        called by Template._codeGenerator() so it doesn't take a templateObj arg."""
        
        token = self.setting('placeholderStartToken')
        return theString.replace('\\' + token, token)
