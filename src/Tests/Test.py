#!/usr/bin/env python
# $Id: Test.py,v 1.41 2002/10/20 09:20:20 hierro Exp $
"""Core module of Cheetah's Unit-testing framework

TODO
================================================================================
# combo tests
# negative test cases for expected exceptions
# black-box vs clear-box testing
# do some tests that run the Template for long enough to check that the refresh code works

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@damnsimple.com>,
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.41 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2002/10/20 09:20:20 $
"""
__author__ = "Tavis Rudd <tavis@damnsimple.com>"
__revision__ = "$Revision: 1.41 $"[11:-2]


##################################################
## DEPENDENCIES ##

import sys
import unittest_local_copy as unittest

##################################################
## CONSTANTS & GLOBALS

try:
    True, False
except NameError:
    True, False = (1==1),(1==0)

##################################################
## TESTS

import SyntaxAndOutput
import NameMapper
import Template
import FileRefresh
import CheetahWrapper

testSuite = unittest.findTestCases(SyntaxAndOutput)
testSuite.addTest( unittest.findTestCases(NameMapper) )
testSuite.addTest( unittest.findTestCases(Template) )
testSuite.addTest( unittest.findTestCases(FileRefresh) )
testSuite.addTest( unittest.findTestCases(CheetahWrapper) )

##################################################
## if run from the command line
if __name__ == '__main__':
    unittest.main(testSuite=testSuite)
    #unittest.TextTestRunner().run(testSuite)



