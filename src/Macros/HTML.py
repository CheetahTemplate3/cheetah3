#!/usr/bin/env python
# $Id: HTML.py,v 1.2 2001/08/08 06:32:16 tavis_rudd Exp $
"""HTML macros for use with Cheetah templates

Meta-Data
==========
Author: Tavis Rudd <tavis@calrudd.com>,
Version: $Revision: 1.2 $
Start Date: 2001/04/05
Last Revision Date: $Date: 2001/08/08 06:32:16 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.2 $"[11:-2]

##################################################
## DEPENDENCIES ##

import time
import types
import os

##################################################
## GLOBALS AND CONSTANTS ##

True = (1==1)
False = (0==1)

##################################################
## FUNCTIONS ##

def currentYr():
    """Return a string representing the current yr."""
    return time.strftime("%Y",time.localtime(time.time()))

def currentDate(formatString="%b %d, %Y"):
    """Return a string representing the current localtime."""
    return time.strftime(formatString,time.localtime(time.time()))

def spacer(width=1,height=1):
    return '<IMG SRC="spacer.gif" WIDTH=%s HEIGHT=%s ALT="">'% (str(width), str(height))

def formHTMLTag(tagName, attributes={}):
    """returns a string containing an HTML <tag> """
    tagTxt = ['<', tagName.upper()]
    for name, val in attributes.items():
        if type(val)==types.StringType:
            val = '"' + val + '"'
        tagTxt += [' ', name.upper(), '=', str(val)]
    tagTxt.append('>')
    return ''.join(tagTxt)

def formatMetaTags(metaTags):
    """format a dict of metaTag definitions into an HTML version"""
    metaTagsTxt = []
    if metaTags.has_key('HTTP_EQUIV'):
        for http_equiv, contents in metaTags['HTTP_EQUIV'].items():
            metaTagsTxt += ['<META HTTP_EQUIV="', str(http_equiv), '" CONTENTS="',
                            str(contents), '">\n']
            
    if metaTags.has_key('NAME'):
        for name, contents in metaTags['NAME'].items():
            metaTagsTxt += ['<META NAME="', str(name), '" CONTENTS="', str(contents),
                            '">\n']
    return ''.join(metaTagsTxt)
