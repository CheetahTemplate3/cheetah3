#!/usr/bin/env python
# $Id: __init__.py,v 1.5 2005/08/16 20:43:52 tavis_rudd Exp $

"""Cheetah is a Python-powered template engine and code-generator.
It is similar to the Jakarta project's Velocity.

Homepage
================================================================================
http://www.CheetahTemplate.org

Mailing list
================================================================================
cheetahtemplate-discuss@lists.sourceforge.net
Subscribe at
http://lists.sourceforge.net/lists/listinfo/cheetahtemplate-discuss

Documentation
================================================================================

For a high-level introduction to Cheetah please refer to the User's Guide
in the docs/ directory of the Cheetah distribution.

Installation
================================================================================
Cheetah can be run a directory in the from the system-wide Python path or
from a directory in a user's Python path.  

To install Cheetah for a single user:
  - copy the 'src' sub-directory to a directory called 'Cheetah' that is in the
  user's PYTHON_PATH

To install Cheetah for system-wide use:
  - on Posix systems (AIX, Solaris, Linux, IRIX, etc.) become the 'root' user
  and run: python ./setup.py install
  
  - On non-posix systems, such as Windows NT, login as an administrator and
  type this at the command-line:  python setup.py install

On Posix systems, the system-wide installation will also install the Cheetah's
command-line compiler program, TScompile, to a system-wide executable path such as
/usr/local/bin.
 

Meta-Data
================================================================================
Authors: The Cheetah Development Team (Tavis Rudd, Mike Orr, Chuck Esterbrook
         Ian Bicking, Tom Schwaller)
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.5 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2005/08/16 20:43:52 $
""" 
__author__ = "Tavis Rudd <tavis@damnsimple.com>"
__revision__ = "$Revision: 1.5 $"[11:-2]

from Version import Version
