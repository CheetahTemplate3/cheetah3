#!/usr/bin/env python
# $Id: CGITemplate.py,v 1.4 2005/01/03 18:11:20 tavis_rudd Exp $
"""A subclass of Cheetah.Template for use in CGI scripts.

Usage in a template:
    #extends Cheetah.Tools.CGITemplate
    #implements respond
    $cgiHeaders#slurp

Usage in a template inheriting a Python class:
1. The template
    #extends MyPythonClass
    #implements respond
    $cgiHeaders#slurp

2. The Python class
    from Cheetah.Tools import CGITemplate
    class MyPythonClass(CGITemplate):
        def cgiHeadersHook(self):
            return "Content-Type: text/html; charset=koi8-r\n\n"

To read GET/POST variables, use the .webInput method defined in
Cheetah.Utils.WebInputMixin (available in all templates without importing
anything), use Python's 'cgi' module, or make your own arrangements.

This class inherits from Cheetah.Template to make it usable in Cheetah's
single-inheritance model.  


Meta-Data
================================================================================
Author: Mike Orr <iron@mso.oz.net>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.4 $
Start Date: 2001/10/03
Last Revision Date: $Date: 2005/01/03 18:11:20 $
""" 
__author__ = "Mike Orr <iron@mso.oz.net>"
__revision__ = "$Revision: 1.4 $"[11:-2]

import os
from Cheetah.Template import Template

class CGITemplate(Template):
    """Methods useful in CGI scripts.

       Any class that inherits this mixin must also inherit Cheetah.Servlet.
    """
    

    def cgiHeaders(self):
        """Outputs the CGI headers if this is a CGI script.

           Usage:  $cgiHeaders#slurp
           Override .cgiHeadersHook() if you want to customize the headers.
        """
        if self.isCgi():
            return self.cgiHeadersHook()



    def cgiHeadersHook(self):
        """Override if you want to customize the CGI headers.
        """
        return "Content-type: text/html\n\n"


    def isCgi(self):
        """Is this a CGI script?
        """
        env = os.environ.has_key('REQUEST_METHOD') 
        wk = self.isControlledByWebKit
        return env and not wk


    
# vim: shiftwidth=4 tabstop=4 expandtab
