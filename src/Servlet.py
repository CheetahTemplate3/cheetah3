#!/usr/bin/env python
# $Id: Servlet.py,v 1.8 2001/10/10 06:47:41 tavis_rudd Exp $
"""Provides an abstract Servlet baseclass for Cheetah's Template class

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.8 $
Start Date: 2001/10/03
Last Revision Date: $Date: 2001/10/10 06:47:41 $
""" 
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.8 $"[11:-2]

##################################################
## CONSTANTS & GLOBALS

True = (1==1)
False = (0==1)

##################################################
## DEPENDENCIES

import os.path

isRunningFromWebKit = False
try: 
    from WebKit.HTTPServlet import HTTPServlet
    isRunningFromWebKit = True
except:
    ## for testing from the commandline or with TR's experimental rewrite of WebKit
    try:
        from Webware.HTTPServlet import HTTPServlet
    except:
        class HTTPServlet: 
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


class Servlet(HTTPServlet):

    def __init__(self):
        HTTPServlet.__init__(self)
        
    ## methods called by Webware during the request-response
        
    def awake(self, transaction):
        self._transaction = transaction
        self._response    = transaction.response()
        self._request     = transaction.request()
        self._session     = None  # don't create unless needed

    def respond(self, trans=None):
        return ''
    
    __str__ = respond

    def sleep(self, transaction):
        self._session = None
        self._request  = None
        self._response = None
        self._transaction = None

    def application(self):
        return self._transaction.application()

    def transaction(self):
        return self._transaction

    def request(self):
        return self._request

    def response(self):
        return self._response

    def session(self):
        if not self._session:
            self._session = self._transaction.session()
        return self._session

    def shutdown(self):
        pass

    def serverSidePath(self, path):
        try:
            return HTTPServlet.serverSidePath(self, path)
        except:
            return os.path.normpath(os.path.abspath(path).replace("\\",'/'))
