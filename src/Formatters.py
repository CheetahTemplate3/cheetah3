#!/usr/bin/env python
# $Id: Formatters.py,v 1.2 2001/08/15 17:49:51 tavis_rudd Exp $
"""Formatters Cheetah's $placeholders

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.2 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/08/15 17:49:51 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.2 $"[11:-2]

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

    
## make an alias
ReplaceNone = BaseClass

class MaxLen(BaseClass):
    def format(self, val, **kw):
        """Replace None with '' and cut off at maxlen."""
        if val == None:
            return ''
        output = str(val)
        if kw.has_key('maxlen') and len(output) > kw['maxlen']:
            return output[:kw['maxlen']]
        return output


class Pager(BaseClass):
    def buildQString(self,varsDict, updateDict):
        finalDict = varsDict.copy()
        finalDict.update(updateDict)
        qString = '?'
        for key, val in finalDict.items():
            qString += str(key) + '=' + str(val) + '&'
        return qString
    
    def format(self, val, **kw):
        """Replace None with '' and cut off at maxlen."""
        if val == None:
            return ''
        output = str(val)
        if kw.has_key('trans') and kw['trans']:
            ID = kw['ID']
            marker = kw.get('marker', '<split>')
            req = kw['trans'].request()
            URI = req.environ()['SCRIPT_NAME'] + req.environ()['PATH_INFO']
            queryVar = 'pager' + str(ID) + '_page'
            fields = req.fields()
            page = int(fields.get( queryVar, 1))
            pages = output.split(marker)
            output = pages[page-1]
            output += '<BR>'
            if page > 1:
                output +='<A HREF="' + URI + self.buildQString(fields, {queryVar:max(page-1,1)}) + \
                          '">Previous Page</A>&nbsp;&nbsp;&nbsp;'
            if page < len(pages):
                output += '<A HREF="' + URI + self.buildQString(
                    fields,
                    {queryVar:
                     min(page+1,len(pages))}) + \
                     '">Next Page</A>' 

            return output
        return output

