#!/usr/bin/env python
# $Id: DummyTransaction.py,v 1.12 2005/01/03 19:46:48 tavis_rudd Exp $

"""Provides dummy Transaction and Response classes is used by Cheetah in place
of real Webware transactions when the Template obj is not used directly as a
Webware servlet.

Meta-Data
==========
Author: Tavis Rudd <tavis@damnsimple.com>
Version: $Revision: 1.12 $
Start Date: 2001/08/30
Last Revision Date: $Date: 2005/01/03 19:46:48 $
"""
__author__ = "Tavis Rudd <tavis@damnsimple.com>"
__revision__ = "$Revision: 1.12 $"[11:-2]

from StringIO import StringIO  # not cStringIO because of Unicode support, and some strange bug

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
       
