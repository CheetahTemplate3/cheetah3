#!/usr/bin/env python
# $Id: Formatters.py,v 1.1 2001/08/14 19:29:50 tavis_rudd Exp $
"""Formatters Cheetah's $placeholders

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.1 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/08/14 19:29:50 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.1 $"[11:-2]

##################################################
## DEPENDENCIES ##

# intra-package imports ...
from Parser import Parser

##################################################
## CONSTANTS & GLOBALS ##

True = (1==1)
False = (0==1)

##################################################
## CLASSES ##

class Error(Exception):
    pass

class BaseClass(Parser):
    """A baseclass for the Cheetah Formatters."""
    
    def __init__(self, templateObj):
        """Setup a ref to the templateObj.  Subclasses should call this method."""
        Parser.__init__(self, templateObj)
    
    def format(self, val, **kw):
        """Replace None with an empty string """
        if val == None:
            return ''
        return str(val)

class MaxLen(BaseClass):
    def format(self, val, **kw):
        """Replace None with '' and cut off at maxlen."""
        if val == None:
            return ''
        output = str(val)
        if kw.has_key('maxlen') and len(output) > kw['maxlen']:
            return output[:kw['maxlen']]
        return output
        
    
## make an alias
Default = BaseClass


