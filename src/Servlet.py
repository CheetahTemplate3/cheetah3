#!/usr/bin/env python
# $Id: Servlet.py,v 1.17 2002/03/13 18:39:07 tavis_rudd Exp $
"""Provides an abstract Servlet baseclass for Cheetah's Template class

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.17 $
Start Date: 2001/10/03
Last Revision Date: $Date: 2002/03/13 18:39:07 $
""" 
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__revision__ = "$Revision: 1.17 $"[11:-2]

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

        def shutdown(self):
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
	self.isRunningFromWebKit = isRunningFromWebKit

        
    ## methods called by Webware during the request-response
        
    def awake(self, transaction):
        BaseServlet.awake(self, transaction)        
        self.transaction = transaction        
        self.application = transaction.application
        self.response = response = transaction.response
        self.request = transaction.request
        self.session = transaction.session
        self.write = response().write
        #self.writeln = response.writeln
        
    def respond(self, trans=None):
        return ''
    
    __str__ = respond

    def sleep(self, transaction):
        BaseServlet.sleep(self, transaction)
        self.session = None
        self.request  = None
        self.response = None
        self.transaction = None

    def shutdown(self):
        pass

    def serverSidePath(self, path=None):
        try:
            return BaseServlet.serverSidePath(self, path)
        except:
            return os.path.normpath(os.path.abspath(path).replace("\\",'/'))
