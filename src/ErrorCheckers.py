#!/usr/bin/env python
# $Id: ErrorCheckers.py,v 1.1 2001/08/14 06:05:20 tavis_rudd Exp $
"""ErrorChecker class Cheetah's codeGenerator

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.1 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/08/14 06:05:20 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.1 $"[11:-2]

##################################################
## DEPENDENCIES ##

import time

# intra-package imports ...
from Parser import Parser
from NameMapper import NotFound


##################################################
## CONSTANTS & GLOBALS ##

True = (1==1)
False = (0==1)

##################################################
## CLASSES ##

class Error(Exception):
    pass

class BaseClass(Parser):

    def __init__(self, templateObj):
        Parser.__init__(self, templateObj)
        self._entries = {}
        
    def set(self, ID, tag, translatedTag):
        self._entries[ID] = (tag, translatedTag) 

    def get(self, ID, trans=None, localsDict={}):
        try:
            val = self.evalPlaceholderString(self._entries[ID][1],
                                             localsDict=localsDict)
            return val
        except NotFound:
            return self.warn(ID, trans=trans, localsDict=localsDict)
        
    def warn(self, ID, **kw):
        return  self._entries[ID][0]

## make an alias
Echo = BaseClass

class BigEcho(BaseClass):
    def warn(self, ID, **kw):
        return "="*15 + "&lt;" + self._entries[ID][0] + " could not be found&gt;" + "="*15

class KeyError(BaseClass):
    def warn(self, ID, **kw):
        raise KeyError("no '%s' in this Template Object's Search List" % self._entries[ID][0]) 


class ListErrors(BaseClass):
    """Accumulate a list of errors."""
    _timeFormat = "%c"
    
    def __init__(self, templateObj):
        BaseClass.__init__(self, templateObj)
        self._errors = []

    def warn(self, ID, **kw):
        self._errors.append({'ID':ID,
                             'time':time.strftime(self._timeFormat,
                                                  time.localtime(time.time()))})
        return self._entries[ID][0]
    
    def listErrors(self):
        """Return the list of tags in the set, sorted."""
        resList = [(self._entries[i['ID']][0], i['time']) for i in self._errors]
        return resList


