#!/usr/bin/env python
# $Id: CheetahWrapper.py,v 1.2 2002/03/13 03:21:27 hierro Exp $
"""A command line interface to everything about Cheetah.

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com> and Mike Orr <iron@mso.oz.net>
Version: $Revision: 1.2 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2002/03/13 03:21:27 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com> and Mike Orr <iron@mso.oz.net>"
__revision__ = "$Revision: 1.2 $"[11:-2]

##################################################
## DEPENDENCIES

import sys
import re
import os
import getopt
import os.path
from glob import glob
import shutil


from _properties import Version

##################################################
## GLOBALS & CONSTANTS

True = (1==1)
False = (1==0)

class Error(Exception):
    pass


class CheetahWrapper:
    """A command-line interface to everything about Cheetah."""
    
    def __init__(self, scriptName=os.path.basename(sys.argv[0]),
                 cmdLineArgs=sys.argv[1:]):

        self._scriptName = scriptName
        self._cmdLineArgs = cmdLineArgs

    def run(self):
        """The main program controller."""

        if len(sys.argv) > 1 and sys.argv[1] in ("compile","-c"):
            ## swap into compile mode then exit            
            from Cheetah.CheetahCompile import CheetahCompile
            del sys.argv[1]
            sys.argv[0] += ' compile'
            CheetahCompile(sys.argv[0], sys.argv[1:]).run()
            sys.exit()
        elif len(sys.argv) > 1 and sys.argv[1] in ("test","-t"):
            ## swap into unittesting mode then exit            
            from Cheetah.Tests import Test
            import Cheetah.Tests.unittest_local_copy as unittest
            del sys.argv[1]
            sys.argv[0] += ' test'
            unittest.main(testSuite=Test.testSuite)
            sys.exit()
        elif '-v' in sys.argv or '--version' in sys.argv:
             print self.version()   
        else:
            print self.usage()

    def version(self):
        return Version
        
    def usage(self):
        return """\
         __  ____________  __
         \ \/            \/ /
          \/    *   *     \/    CHEETAH %(Version)s Command-Line Tool
           \      |       / 
            \  ==----==  /      by Tavis Rudd <tavis@calrudd.com>
             \__________/       and Mike Orr <iron@mso.oz.net>
              
USAGE        
-----
%(script)s --help|-h            
          - Print this usage information
%(script)s compile|-c [compiler options]
          - Run Cheetah's compiler ('%(script)s compile --help' for more)
%(script)s test|-t [test options]
          - Run Cheetah's test suite ('%(script)s test --help' for more)
%(script)s --version|-v
          - Print Cheetah's version number

    [Think you can draw a better ASCII-art cheetah face?  Do it!
     See http://www.cheetahtemplate.org/cheetah-face-black-medium.jpg 
     and send the result to iron@mso.oz.net. ]
""" % {'script':self._scriptName,
       'Version':Version,
       'author':__author__,
       }
   
##################################################
## if run from the command line
if __name__ == '__main__':

    CheetahWrapper().run()

# vim: expandtab
