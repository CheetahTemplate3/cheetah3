#!/usr/bin/env python
# $Id: Utilities.py,v 1.5 2001/08/10 18:46:22 tavis_rudd Exp $
"""Utility classes and functions used in the Cheetah package


Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.5 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2001/08/10 18:46:22 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.5 $"[11:-2]


##################################################
## DEPENDENCIES ##

import re
import types

##################################################
## CONSTANTS & GLOBALS ##

True = (1==1)
False = (0==1)

class Error(Exception): pass

##################################################
## FUNCTIONS ##

def separateTagsFromText(initialText, startTagRE, endTagRE):
    """breaks a string up into a textVsTagsList where the odd items are plain
    text and the even items are the contents of the tags."""

    chunks = startTagRE.split(initialText)
    textVsTagsList = []
    for chunk in chunks:
        textVsTagsList.extend(endTagRE.split(chunk))
    return textVsTagsList

def processTextVsTagsList(textVsTagsList, tagProcessorFunction):
    """loops through textVsTagsList - the output from separateTagsFromText() -
    and filters all the tag items with the tagProcessorFunction"""
    
    ## odd items are plain text, even ones are tags
    processedList = textVsTagsList[:]
    for i in range(1, len(processedList), 2):
        processedList[i] = tagProcessorFunction(processedList[i])
    return processedList

def insertLineNums(string):
    """Return a version of the string with each line prefaced with its line
     number."""
     
    string = str(string)
    lineNum = [0,]
    def lineNums(match, lineNum=lineNum):
        lineNum[0] +=1
        return "%(match)s%(line)-3d|"% {'match':match.group(), 'line':lineNum[0]}

    if string.find('\n') != -1:
        return re.sub(r'^|\n', lineNums, string)
    else:
        return "1 |" + string

def getLines(string, sliceObj):
    """Slice a string up into a list of lines and return a slice."""
    lines = string.split('\n')
    return lines[lineNums]

def lineNumFromPos(string, pos):
    """Calculate what line a position in a string lies on. This doesn't work on
     Mac-OS."""
    
    return len(string[0:pos].split('\n'))


def unique(s):
    """Return a list of the elements in s, but without duplicates.

    For example, unique([1,2,3,1,2,3]) is some permutation of [1,2,3],
    unique("abcabc") some permutation of ["a", "b", "c"], and
    unique(([1, 2], [2, 3], [1, 2])) some permutation of
    [[2, 3], [1, 2]].

    For best speed, all sequence elements should be hashable.  Then
    unique() will usually work in linear time.

    If not possible, the sequence elements should enjoy a total
    ordering, and if list(s).sort() doesn't raise TypeError it's
    assumed that they do enjoy a total ordering.  Then unique() will
    usually work in O(N*log2(N)) time.

    If that's not possible either, the sequence elements must support
    equality-testing.  Then unique() will usually work in quadratic
    time.

    This method was copied from Tim Peter's contribution to The Python Cookbook.
    """

    n = len(s)
    if n == 0:
        return []

    # Try using a dict first, as that's the fastest and will usually
    # work.  If it doesn't work, it will usually fail quickly, so it
    # usually doesn't cost much to *try* it.  It requires that all the
    # sequence elements be hashable, and support equality comparison.
    u = {}
    try:
        for x in s:
            u[x] = 1
    except TypeError:
        del u  # move on to the next method
    else:
        return u.keys()

    # We can't hash all the elements.  Second fastest is to sort,
    # which brings the equal elements together; then duplicates are
    # easy to weed out in a single pass.
    # NOTE:  Python's list.sort() was designed to be efficient in the
    # presence of many duplicate elements.  This isn't true of all
    # sort functions in all languages or libraries, so this approach
    # is more effective in Python than it may be elsewhere.
    try:
        t = list(s)
        t.sort()
    except TypeError:
        del t  # move on to the next method
    else:
        assert n > 0
        last = t[0]
        lasti = i = 1
        while i < n:
            if t[i] != last:
                t[lasti] = last = t[i]
                lasti += 1
            i += 1
        return t[:lasti]

    # Brute force is all that's left.
    u = []
    for x in s:
        if x not in u:
            u.append(x)
    return u

def mergeNestedDictionaries(dict1, dict2):
    """Recursively merge the values of dict2 into dict1.

    This little function is very handy for selectively overriding settings in a
    settings dictionary that has a nested structure.  """

    newDict = dict1.copy()
    for key,val in dict2.items():
        if newDict.has_key(key) and type(val) == types.DictType and type(newDict[key]) == types.DictType:
            newDict[key] = mergeNestedDictionaries(newDict[key], val)
        else:
            newDict[key] = val
    return newDict



##################################################
## CLASSES ##

#none yet

##################################################
## if run from the command line ##

if __name__ == '__main__':
    pass

