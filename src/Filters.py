#!/usr/bin/env python
# $Id: Filters.py,v 1.6 2001/11/10 19:50:02 hierro Exp $
"""Filters for the #filter directive; output filters Cheetah's $placeholders .

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
Version: $Revision: 1.6 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/11/10 19:50:02 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.6 $"[11:-2]

##################################################
## DEPENDENCIES

# intra-package imports ...

##################################################
## CONSTANTS & GLOBALS

True = (1==1)
False = (0==1)

# Additional entities WebSafe knows how to transform.  No need to include
# '<', '>' or '&' since those will have been done already.
webSafeEntities = {' ': '&nbsp;', '"': '&quot;'}

##################################################
## CLASSES

class Error(Exception):
    pass

class NoDefault:
    pass


class DummyTemplate:
    """Fake template class to allow filters to be used standalone.
    """
    def setting(self, name, default=NoDefault):
        if default is NoDefault:
            raise KeyError(name)
        else:
            return default

    def settings(self):
        return {}

_dummyTemplateObj = DummyTemplate()


class Filter:
    """A baseclass for the Cheetah Filters."""
    
    def __init__(self, templateObj=_dummyTemplateObj):
        """Setup a ref to the templateObj.  Subclasses should call this method.
        """
        self.setting = templateObj.setting
        self.settings = templateObj.settings

    def generateAutoArgs(self):
        
        """This hook allows the filters to generate an arg-list that will be
        appended to the arg-list of a $placeholder tag when it is being
        translated into Python code during the template compilation process. See
        the 'Pager' filter class for an example."""
        
        return ''
        
    def filter(self, val, **kw):
        
        """Replace None with an empty string.  Reimplement this method if you
        want more advanced filterting."""
        
        if val == None:
            return ''
        return str(val)

    
## make an alias
ReplaceNone = Filter

class MaxLen(Filter):
    def filter(self, val, **kw):
        """Replace None with '' and cut off at maxlen."""
        output = Filter.filter(self, val, **kw)
        if kw.has_key('maxlen') and len(output) > kw['maxlen']:
            return output[:kw['maxlen']]
        return output


class Pager(Filter):
    def __init__(self, templateObj=_dummyTemplateObj):
        Filter.__init__(self, templateObj)
        self._IDcounter = 0
        
    def buildQString(self,varsDict, updateDict):
        finalDict = varsDict.copy()
        finalDict.update(updateDict)
        qString = '?'
        for key, val in finalDict.items():
            qString += str(key) + '=' + str(val) + '&'
        return qString

    def generateAutoArgs(self):
        ID = str(self._IDcounter)
        self._IDcounter += 1
        return ', trans=trans, ID=' + ID
    
    def filter(self, val, **kw):
        """Replace None with '' and cut off at maxlen."""
        output = Filter.filter(self, val, **kw)
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


class WebSafe(Filter):
    """Escape HTML entities in $placeholders.
    """
    def filter(self, val, **kw):
        # Do the default conversion.
        s = Filter.filter(self, val, **kw)
        # These substitutions are copied from cgi.escape().
        s = s.replace("&", "&amp;") # Must be done first!
        s = s.replace("<", "&lt;")
        s = s.replace(">", "&gt;")
        # Process the additional transformations if any.
        if kw.has_key('also'):
            also = kw['also']
            entities = webSafeEntities   # Global variable.
            for k in also:
                if entities.has_key(k):
                    v = entities[k]
                else:
                    v = "&#%s;" % ord(k)
                s = s.replace(k, v)
        # Return the puppy.
        return s


class Strip(Filter):
    """Strip leading/trailing whitespace but preserve trailing newline.
    """
    def filter(self, val, **kw):
        if val[-1:] == '\n':
            val = val[:-1]
            eol = '\n'
        else:
            eol = ''
        return val.strip() + eol


# class StripSqueeze -- same as strip but also convert newlines -> ' '.
# Implementation delayed till we decide if there's a use for it.

# vim: shiftwidth=4 tabstop=4 expandtab
