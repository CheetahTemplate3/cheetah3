#!/usr/bin/env python
# $Id: TemplateMisc.py,v 1.2 2002/06/08 03:45:44 hierro Exp $
"""Convenience methods for Template that don't depend on Webware.

Meta-Data
================================================================================
Author: Mike Orr <iron@mso.oz.net>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.2 $
Start Date: 2001/10/03
Last Revision Date: $Date: 2002/06/08 03:45:44 $
""" 
__author__ = "Mike Orr <iron@mso.oz.net>"
__revision__ = "$Revision: 1.2 $"[11:-2]

##################################################
## CONSTANTS & GLOBALS

try:
    True,False
except NameError:
    True, False = (1==1),(1==0)

##################################################
## DEPENDENCIES

import os
from Cheetah.Utils.CGIImportMixin import CGIImportMixin


##################################################
## CLASSES

class TemplateMisc(CGIImportMixin):
    """Convenience methods for Cheetah.Template that don't require Webware.

       Any class that inherits this mixin must also inherit Cheetah.Servlet.
    """
    
    def cgiHeaders(self):
        """Outputs the CGI headers if this appears to be a CGI script.

           Usage:  $cgiHeaders#slurp
           Override .cgiHeadersHook() if you want to customize the headers.
        """
        isCgi = os.environ.has_key('REQUEST_METHOD')
        if isCgi and not self.isControlledByWebKit:
            return self.cgiHeadersHook()


    def cgiHeadersHook(self):
        """Override if you want to customize the CGI headers.
        """
        return "Content-type: text/html\n\n"


# vim: shiftwidth=4 tabstop=4 expandtab
