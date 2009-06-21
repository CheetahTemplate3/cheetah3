'''
Provides an abstract Servlet baseclass for Cheetah's Template class
'''

import sys
import os.path

isWebwareInstalled = False
try:
    try:
        from ds.appserver.Servlet import Servlet as BaseServlet
    except:
        from WebKit.Servlet import Servlet as BaseServlet
    isWebwareInstalled = True

    if not issubclass(BaseServlet, object):
        class NewStyleBaseServlet(BaseServlet, object):
            pass
        BaseServlet = NewStyleBaseServlet
except:
    class BaseServlet(object): 
        _reusable = 1
        _threadSafe = 0
    
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
    
    def __init__(self, *args, **kwargs):
        super(Servlet, self).__init__(*args, **kwargs)
       
        # this default will be changed by the .awake() method
        self._CHEETAH__isControlledByWebKit = False 
        
    ## methods called by Webware during the request-response
        
    def awake(self, transaction):
        super(Servlet, self).awake(transaction)
        
        # a hack to signify that the servlet is being run directly from WebKit
        self._CHEETAH__isControlledByWebKit = True
        
        self.transaction = transaction        
        #self.application = transaction.application
        self.response = response = transaction.response
        self.request = transaction.request

        # Temporary hack to accomodate bug in
        # WebKit.Servlet.Servlet.serverSidePath: it uses 
        # self._request even though this attribute does not exist.
        # This attribute WILL disappear in the future.
        self._request = transaction.request()

        
        self.session = transaction.session
        self.write = response().write
        #self.writeln = response.writeln
        
    def respond(self, trans=None):
        raise NotImplementedError("""\
couldn't find the template's main method.  If you are using #extends
without #implements, try adding '#implements respond' to your template
definition.""")

    def sleep(self, transaction):
        super(Servlet, self).sleep(transaction)
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
        
        if self._CHEETAH__isControlledByWebKit:
            return super(Servlet, self).serverSidePath(path)
        elif path:
            return normpath(abspath(path.replace("\\",'/')))
        elif hasattr(self, '_filePath') and self._filePath:
            return normpath(abspath(self._filePath))
        else:
            return None

# vim: shiftwidth=4 tabstop=4 expandtab
