#!/usr/bin/env python
# $Id: CodeGenerator.py,v 1.29 2001/08/11 04:57:39 tavis_rudd Exp $
"""Utilities, processors and filters for Cheetah's codeGenerator

Cheetah's codeGenerator is designed to be extensible with plugin
functions.  This module contains the default plugins.

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.29 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2001/08/11 04:57:39 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.29 $"[11:-2]

##################################################
## DEPENDENCIES ##

import re
import types
from time import time as currentTime # used in the cache refresh code

# intra-package imports ...
import TagProcessor
import NameMapper
from Delimiters import delimiters
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


##################################################
## FUNCTIONS ##

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
