#!/usr/bin/env python
# $Id: Misc.py,v 1.4 2002/06/23 19:32:10 hierro Exp $
"""Miscellaneous functions/objects used by Cheetah but also useful standalone.

Meta-Data
================================================================================
Author: Mike Orr <iron@mso.oz.net>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.4 $
Start Date: 2001/11/07
Last Revision Date: $Date: 2002/06/23 19:32:10 $
""" 
__author__ = "Mike Orr <iron@mso.oz.net>"
__revision__ = "$Revision: 1.4 $"[11:-2]

##################################################
## DEPENDENCIES

import types       # Used in UseOrRaise.

##################################################
## PRIVATE FUNCTIONS


##################################################
## MISCELLANEOUS FUNCTIONS

#!/usr/bin/env python
# $Id: Misc.py,v 1.4 2002/06/23 19:32:10 hierro Exp $
"""Miscellaneous functions/objects used by Cheetah but also useful standalone.

Meta-Data
================================================================================
Author: Mike Orr <iron@mso.oz.net>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.4 $
Start Date: 2001/11/07
Last Revision Date: $Date: 2002/06/23 19:32:10 $
""" 
__author__ = "Mike Orr <iron@mso.oz.net>"
__revision__ = "$Revision: 1.4 $"[11:-2]

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

def CheckKeywords(dic, legalKeywords, what='argument'):
    """Verify no illegal keyword arguments were passed to a function.

    in : dic, dictionary (**kw in the calling routine).
         legalKeywords, list of strings, the keywords that are allowed.
         what, string, suffix for error message (see function source).
    out: None.
    exc: TypeError if 'dic' contains a key not in 'legalKeywords'.
    called by: Cheetah.Template.__init__()
    """
    # XXX legalKeywords could be a set when sets get added to Python.
    for k in dic.keys(): # Can be dic.iterkeys() if Python >= 2.2.
        if k not in legalKeywords: 
            raise TypeError("'%s' is not a valid %s" % (k, what))


# vim: shiftwidth=4 tabstop=4 expandtab
