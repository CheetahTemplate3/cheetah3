#!/usr/bin/env python
# $Id: CheetahCompile.py,v 1.3 2002/03/06 22:01:16 tavis_rudd Exp $
"""Tests of the cheetah-compile tool.

THIS TEST MODULE IS JUST A SHELL AT THE MOMENT. Feel like filling it in??

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>,
Version: $Revision: 1.3 $
Start Date: 2001/10/01
Last Revision Date: $Date: 2002/03/06 22:01:16 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__revision__ = "$Revision: 1.3 $"[11:-2]


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
