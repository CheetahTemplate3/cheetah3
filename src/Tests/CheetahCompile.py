#!/usr/bin/env python
# $Id: CheetahCompile.py,v 1.5 2002/04/15 06:22:53 tavis_rudd Exp $
"""Tests of the cheetah-compile tool.

THIS TEST MODULE IS JUST A SHELL AT THE MOMENT. Feel like filling it in??

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>,
Version: $Revision: 1.5 $
Start Date: 2001/10/01
Last Revision Date: $Date: 2002/04/15 06:22:53 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__revision__ = "$Revision: 1.5 $"[11:-2]


##################################################
## DEPENDENCIES ##

import sys
import types
import os
import os.path

import unittest_local_copy as unittest
from Cheetah.CheetahCompile import CheetahCompile

##################################################
## CONSTANTS & GLOBALS ##

try:
    True,False
except NameError:
    True, False = (1==1),(1==0)

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
