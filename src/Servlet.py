#!/usr/bin/env python
# $Id: Servlet.py,v 1.29 2002/06/30 22:05:37 tavis_rudd Exp $
"""Provides an abstract Servlet baseclass for Cheetah's Template class

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.29 $
Start Date: 2001/10/03
Last Revision Date: $Date: 2002/06/30 22:05:37 $
""" 
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__revision__ = "$Revision: 1.29 $"[11:-2]

##################################################
## CONSTANTS & GLOBALS

try:
    True,False
except NameError:
    True, False = (1==1),(1==0)

##################################################
## DEPENDENCIES

import os.path

isWebwareInstalled = False
try: 
    from WebKit.Servlet import Servlet as BaseServlet
    isWebwareInstalled = True
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
    
    """This class is an abstract baseclass for Cheetah.Template.Template.

    It wraps WebKit.Servlet and provides a few extra convenience methods that
    are also found in WebKit.Page.  It doesn't do any of the HTTP method
    resolution that is done in WebKit.HTTPServlet
    """
    
    transaction = None
    application = None
    request = None
    session = None
    
    def __init__(self):
        BaseServlet.__init__(self)
       
        # this default will be changed by the .awake() method
	self.isControlledByWebKit = False 
        
    ## methods called by Webware during the request-response
        
    def awake(self, transaction):
        BaseServlet.awake(self, transaction)
        
        # a hack to signify that the servlet is being run directly from WebKit
        self.isControlledByWebKit = True
        
        self.transaction = transaction        
        self.application = transaction.application
        self.response = response = transaction.response
        self.request = transaction.request

        # temporary hack to accomodate bug in WebKit.Servlet.Servlet.serverSidePath
        # this attribute WILL disappear in the future
        self._request = transaction.request()

        
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
        self._request  = None        
        self.response = None
        self.transaction = None

    def shutdown(self):
        pass

    def serverSidePath(self, path=None,
                       normpath=os.path.normpath,
                       abspath=os.path.abspath
                       ):
        
        if self.isControlledByWebKit:
            return BaseServlet.serverSidePath(self, path)
        elif path:
            return normpath(abspath(path.replace("\\",'/')))
        elif hasattr(self, '_filePath') and self._filePath:
            return normpath(abspath(self._filePath))
        else:
            return None

