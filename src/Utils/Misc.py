#!/usr/bin/env python
# $Id: Misc.py,v 1.2 2002/03/17 21:03:39 hierro Exp $
"""Miscellaneous functions/objects used by Cheetah but also useful standalone.

Meta-Data
================================================================================
Author: Mike Orr <iron@mso.oz.net>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.2 $
Start Date: 2001/11/07
Last Revision Date: $Date: 2002/03/17 21:03:39 $
""" 
__author__ = "Mike Orr <iron@mso.oz.net>"
__revision__ = "$Revision: 1.2 $"[11:-2]

##################################################
## DEPENDENCIES

import types       # Used in UseOrRaise.

##################################################
## PRIVATE FUNCTIONS


##################################################
## MISCELLANEOUS FUNCTIONS

def UseOrRaise(thing, errmsg=''):
    """Raise 'thing' if it's a subclass of Exception.  Otherwise return it.

    Called by: Cheetah.Servlet.cgiImport()
    """
    if type(thing) == types.ClassType and issubclass(thing, Exception):
        raise thing(errmsg)
    return thing


# vim: shiftwidth=4 tabstop=4 expandtab
