#!/usr/bin/env python
# $Id: Servlet.py,v 1.5 2001/08/10 04:51:31 tavis_rudd Exp $
"""An abstract base class for Cheetah Servlets that can be used with Webware

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>,
Version: $Revision: 1.5 $
Start Date: 2001/04/05
Last Revision Date: $Date: 2001/08/10 04:51:31 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.5 $"[11:-2]

##################################################
## DEPENDENCIES ##

import types

# intra-package imports ...
from Template import Template
from Utilities import mergeNestedDictionaries
import CodeGenerator as CodeGen

##################################################
## GLOBALS AND CONSTANTS ##

True = (1==1)
False = (0==1)

##################################################
## CLASSES ##


isRunningFromWebKit = False
try: 
    from WebKit.HTTPServlet import HTTPServlet
    isRunningFromWebKit = True
except:
    ## for testing from the commandline or with TR's experimental rewrite of WebKit
    
    class HTTPServlet: 
        _reusable = 1
        _threadSafe = 0

        def __init__(self):
            pass
        
        def awake(self, transaction):
            pass
        
        def sleep(self, transaction):
            pass

class TemplateServlet(Template, HTTPServlet):
    """An abstract base class for Cheetah servlets that can be used with
    Webware"""
   
    def __init__(self, template='', *searchList, **kw):
        """ """
        if not kw.has_key('settings'):
            kw['settings']={}
        kw['settings']['delayedCompile'] = True
        Template.__init__(self, template, *searchList, **kw)
        HTTPServlet.__init__(self)
        self.initializeTemplate()
        self._isCompiled = False
        
        if not isRunningFromWebKit:
            self._isCompiled = True
            self.compileTemplate()


    def initializeTemplate(self):
        """a hook that can be used by subclasses to do things after the
        Template has been initialized, but before it has been started
        (i.e. before the codeGeneration process starts) """
        pass

    def awake(self, transaction):
        self._transaction = transaction
        self._response    = transaction.response()
        self._request     = transaction.request()
        self._session     = None  # don't create unless needed
        if not self._isCompiled:
            self._isCompiled = True
            self.compileTemplate()

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
            
    def normalizePath(self, path):
        """A hook for any neccessary path manipulations.

        For example, when this is used with Webware servlets all relative paths
        must be converted so they are relative to the servlet's directory rather
        than relative to the program's current working dir.

        The default implementation just normalizes the path for the current
        operating system."""

        if hasattr(self,'serverSidePath'):
            return self.serverSidePath(path)
        else:
            return os.path.normpath(path.replace("\\",'/'))


