#!/usr/bin/env python
# $Id: ErrorCatchers.py,v 1.5 2002/04/15 06:22:53 tavis_rudd Exp $
"""ErrorCatcher class for Cheetah Templates

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
Version: $Revision: 1.5 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2002/04/15 06:22:53 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__revision__ = "$Revision: 1.5 $"[11:-2]

##################################################
## DEPENDENCIES

import time

from NameMapper import NotFound

##################################################
## CONSTANTS & GLOBALS

try:
    True,False
except NameError:
    True, False = (1==1),(1==0)

##################################################
## CLASSES

class Error(Exception):
    pass

class ErrorCatcher:
    _exceptionsToCatch = (NotFound,)
    
    def __init__(self, templateObj):
        pass
    
    def exceptions(self):
        return self._exceptionsToCatch
    
    def warn(self, exc_val, code, rawCode, lineCol):
        return rawCode
    

## make an alias
Echo = ErrorCatcher

class BigEcho(ErrorCatcher):
    def warn(self, exc_val, code, rawCode, lineCol):
        return "="*15 + "&lt;" + rawCode + " could not be found&gt;" + "="*15

class KeyError(ErrorCatcher):
    def warn(self, exc_val, code, rawCode, lineCol):
        raise KeyError("no '%s' in this Template Object's Search List" % rawCode) 

class ListErrors(ErrorCatcher):
    """Accumulate a list of errors."""
    _timeFormat = "%c"
    
    def __init__(self, templateObj):
        ErrorCatcher.__init__(self, templateObj)
        self._errors = []

    def warn(self, exc_val, code, rawCode, lineCol):
        dict = locals().copy()
        del dict['self']
        dict['time'] = time.strftime(self._timeFormat,
                                     time.localtime(time.time()))
        self._errors.append(dict)
        return rawCode
    
    def listErrors(self):
        """Return the list of errors."""
        return self._errors


