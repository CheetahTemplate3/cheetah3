#!/usr/bin/env python
# $Id: Components.py,v 1.1 2001/06/13 03:50:39 tavis_rudd Exp $
"""Components that can be used with the Cheetah component framework

See the Cheetah User's Guide for more information on components.

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.1 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2001/06/13 03:50:39 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.1 $"[11:-2]


##################################################
## CLASSES ##

class Component:
    """an abstract base-class for Cheetah components"""

    def __call__(self, transaction=None, templateObj=None):
        """this method is called by the Cheetah when a component is embedded
        in a template.  Each component must reimplement this method.

        In order to allow command-line debugging, the component should be equiped with
        default settings to handle cases where the transaction==None.  The code below
        is a silly example"""

        if transaction:
            return 'component called: ' + str( transaction.request().fields() )
        else:
            return 'component called'


