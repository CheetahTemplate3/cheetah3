#!/usr/bin/env python
# $Id: FileRefresh.py,v 1.4 2002/04/15 06:12:19 tavis_rudd Exp $
"""Tests to make sure that the file-update-monitoring code is working properly

THIS TEST MODULE IS JUST A SHELL AT THE MOMENT. Feel like filling it in??

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>,
Version: $Revision: 1.4 $
Start Date: 2001/10/01
Last Revision Date: $Date: 2002/04/15 06:12:19 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__revision__ = "$Revision: 1.4 $"[11:-2]


##################################################
## DEPENDENCIES ##

import sys
import types
import os
import os.path


import unittest_local_copy as unittest
from Cheetah.Template import Template

##################################################
## CONSTANTS & GLOBALS ##

try:
    True = (1==1)
    False = (0==1)
except:
    pass

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
