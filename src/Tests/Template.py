#!/usr/bin/env python
# $Id: Template.py,v 1.3 2001/10/10 06:57:22 tavis_rudd Exp $
"""Tests of the Template class API

THIS TEST MODULE IS JUST A SHELL AT THE MOMENT. Feel like filling it in??

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>,
Version: $Revision: 1.3 $
Start Date: 2001/10/01
Last Revision Date: $Date: 2001/10/10 06:57:22 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.3 $"[11:-2]


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
    from src.Template import Template
elif os.path.exists(os.path.join(newPath, 'Cheetah')):
    from Cheetah.Template import Template
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
