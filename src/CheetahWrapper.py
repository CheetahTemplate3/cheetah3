#!/usr/bin/env python
# $Id: CheetahWrapper.py,v 1.1 2002/03/07 04:47:33 tavis_rudd Exp $
"""A command line interface to everything about Cheetah.

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
Version: $Revision: 1.1 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2002/03/07 04:47:33 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__revision__ = "$Revision: 1.1 $"[11:-2]

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
## GLOBALS & CONTANTS

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

        if len(sys.argv) > 1 and sys.argv[1] in ("compile",):
            ## swap into compile mode then exit            
            from Cheetah.CheetahCompile import CheetahCompile
            del sys.argv[1]
            sys.argv[0] += ' compile'
            CheetahCompile(sys.argv[0], sys.argv[1:]).run()
            sys.exit()
        elif len(sys.argv) > 1 and sys.argv[1] in ("test",):
            ## swap into unittesting mode then exit            
            from Cheetah.Tests import Test
            import Cheetah.Tests.unittest_local_copy as unittest
            del sys.argv[1]
            sys.argv[0] += ' test'
            unittest.main(testSuite=Test.testSuite)
            sys.exit()
        elif '-v' in sys.argv:
             print self.version()   
        else:
            print self.usage()

    def version(self):
        return Version
        
    def usage(self):
        return """Cheetah %(Version)s command-line tool by %(author)s

USAGE
-----
%(script)s -h | %(script)s --help
  - Print this usage information

%(script)s compile [compiler options]
  - Run Cheetah's compiler ('%(script)s compile --help' for more)

%(script)s test [test options]
  - Run Cheetah's test suite ('%(script)s test --help' for more)
       
%(script)s -v | %(script)s --version 
  - Print Cheetah's version number
  
""" % {'script':self._scriptName,
       'Version':Version,
       'author':'Tavis Rudd',
       }
   
##################################################
## if run from the command line
if __name__ == '__main__':

    CheetahWrapper().run()

