#!/usr/bin/env python
# $Id: Servlet.py,v 1.13 2002/02/26 02:03:53 tavis_rudd Exp $
"""Provides an abstract Servlet baseclass for Cheetah's Template class

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.13 $
Start Date: 2001/10/03
Last Revision Date: $Date: 2002/02/26 02:03:53 $
""" 
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__revision__ = "$Revision: 1.13 $"[11:-2]

##################################################
## CONSTANTS & GLOBALS

True = (1==1)
False = (0==1)

##################################################
## DEPENDENCIES

import os.path

isRunningFromWebKit = False
try: 
    from WebKit.Servlet import Servlet as BaseServlet
    isRunningFromWebKit = True
except:
    class BaseServlet: 
        _reusable = 1
        _threadSafe = 0
    
        def __init__(self):
            pass
            
        def awake(self, transaction):
            pass
            
        def sleep(self, transaction):
            pass

##################################################
## CLASSES


class Servlet(BaseServlet):
    
    transaction = None
    application = None
    request = None
    _session = None
    
    def __init__(self):
        BaseServlet.__init__(self)
        
    ## methods called by Webware during the request-response
        
    def awake(self, transaction):
        self.transaction = transaction        
        self.application = transaction.application()
        self.response    = response = transaction.response()
        self.request     = transaction.request()
        self._session     = None  # don't create unless needed
        self.write = response.write
        #self.writeln = response.writeln
        
    def respond(self, trans=None):
        return ''
    
    __str__ = respond

    def sleep(self, transaction):
        self._session = None
        self.request  = None
        self.response = None
        self.transaction = None

    def session(self):
        if not self._session:
            self._session = self._transaction.session()
        return self._session

    def shutdown(self):
        pass

    def serverSidePath(self, path=None):
        try:
            return BaseServlet.serverSidePath(self, path)
        except:
            return os.path.normpath(os.path.abspath(path).replace("\\",'/'))
