#!/usr/bin/env python
# $Id: Utilities.py,v 1.2 2001/07/09 02:36:24 echuck Exp $
"""Utility classes and functions used in the Cheetah package


Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.2 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2001/07/09 02:36:24 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.2 $"[11:-2]


##################################################
## DEPENDENCIES ##

import re
import types

##################################################
## CONSTANTS & GLOBALS ##

True = (1==1)
False = (0==1)

##################################################
## FUNCTIONS ##

def insertLineNums(string):
    string = str(string)
    lineNum = [0,]
    def lineNums(match, lineNum=lineNum):
        lineNum[0] +=1
        return "%(match)s%(line)-3d|"% {'match':match.group(), 'line':lineNum[0]}

    if string.find('\n') != -1:
        return re.sub(r'^|\n', lineNums, string)
    else:
        return "1 |" + string

def getLines(string, lineNums):
    lines = string.split('\n')
    return lines[lineNums]

def lineNumFromPos(string, pos):
    return len(string[0:pos].split('\n'))


def removeDuplicateValues(list):
    """remove all duplicate values in a list"""
    listCopy = []
    while len(list) > 0:
        if not list[0] in listCopy:
            listCopy.append(list[0])
        del list[0]

    return listCopy

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

