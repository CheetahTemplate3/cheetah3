#!/usr/bin/env python
# $Id: DummyTransaction.py,v 1.6 2002/04/03 17:39:36 tavis_rudd Exp $

"""Provides dummy Transaction and Response classes is used by Cheetah in place
of real Webware transactions when the Template obj is not used directly as a
Webware servlet.

Meta-Data
==========
Author: Tavis Rudd <tavis@calrudd.com>
Version: $Revision: 1.6 $
Start Date: 2001/08/30
Last Revision Date: $Date: 2002/04/03 17:39:36 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__revision__ = "$Revision: 1.6 $"[11:-2]

##################################################
## DEPENDENCIES

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

##################################################
## CONSTANTS & GLOBALS

True = (1==1)
False = (1==0)

##################################################
## CLASSES

class DummyResponse:
    
    """A dummy Response class is used by Cheetah in place of real Webware
    Response objects when the Template obj is not used directly as a Webware
    servlet.  """

    
    def __init__(self):
        self._stringIO = StringIO()
        self.write = self._stringIO.write
        self.flush = self._stringIO.flush
        self.getvalue = self._stringIO.getvalue

        # this might be used for output buffering at some stage in Cheetah
        # but isn't yet.
        self.writelines = self._stringIO.writelines
        
    def writeln(self, txt):
        self.write(txt + '\n')

class DummyTransaction:

    """A dummy Transaction class is used by Cheetah in place of real Webware
    transactions when the Template obj is not used directly as a Webware
    servlet.

    It only provides a response object and method.  All other methods and
    attributes make no sense in this context.  """
    
    def __init__(self):
        self._response = DummyResponse()

    def response(self):
        """Return a ref to the dummy reponse object."""
        return self._response
       
