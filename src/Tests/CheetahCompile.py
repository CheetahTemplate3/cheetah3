#!/usr/bin/env python
# $Id: CheetahCompile.py,v 1.1 2001/11/05 06:50:27 tavis_rudd Exp $
"""Tests of the cheetah-compile tool.

THIS TEST MODULE IS JUST A SHELL AT THE MOMENT. Feel like filling it in??

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>,
Version: $Revision: 1.1 $
Start Date: 2001/10/01
Last Revision Date: $Date: 2001/11/05 06:50:27 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.1 $"[11:-2]


##################################################
## DEPENDENCIES ##

import sys
import types
import os
import os.path
import unittest_local_copy as unittest

# We exist in src/Tests (uninstalled) or Cheetah/Tests (installed)
# Here we fix up sys.path to make sure we get the Cheetah we
# belong to and not some other Cheetah.

newPath = os.path.abspath(os.path.join(os.pardir, os.pardir))
sys.path.insert(1, newPath)

if os.path.exists(os.path.join(newPath, 'src')):
    from src.CheetahCompile import CheetahCompile
elif os.path.exists(os.path.join(newPath, 'Cheetah')):
    from Cheetah.CheetahCompile import CheetahCompile
else:
    raise Exception, "Not sure where to find Cheetah. I do not see src/ or" + \
	  " Cheetah/ two directories up."

##################################################
## CONSTANTS & GLOBALS ##

True = (1==1)
False = (0==1)


##################################################
## TEST DATA FOR USE IN THE TEMPLATES ##

##################################################
## TEST BASE CLASSES

class TemplateTest(unittest.TestCase):
    pass

##################################################
## TEST CASE CLASSES


##################################################
## if run from the command line ##
        
if __name__ == '__main__':
    unittest.main()
