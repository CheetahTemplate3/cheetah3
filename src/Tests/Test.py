#!/usr/bin/env python
# $Id: Test.py,v 1.34 2002/03/07 04:02:42 tavis_rudd Exp $
"""Core module of Cheetah's Unit-testing framework

TODO
================================================================================
# combo tests
# negative test cases for expected exceptions
# black-box vs clear-box testing
# do some tests that run the Template for long enough to check that the refresh code works

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>,
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.34 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2002/03/07 04:02:42 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__revision__ = "$Revision: 1.34 $"[11:-2]


##################################################
## DEPENDENCIES ##

import sys
import unittest_local_copy as unittest

##################################################
## CONSTANTS & GLOBALS

True = (1==1)
False = (0==1)

##################################################
## CLASSES
class RunTests:
    def __init__(self):
        pass
    def run(self):
        import SyntaxAndOutput
        suite = unittest.findTestCases(SyntaxAndOutput)
        
        import NameMapper
        suite.addTest( unittest.findTestCases(NameMapper) )
        
        import Template
        suite.addTest( unittest.findTestCases(Template) )
        
        import CheetahCompile
        suite.addTest( unittest.findTestCases(CheetahCompile) )
    
        import FileRefresh
        suite.addTest( unittest.findTestCases(FileRefresh) )
        
        unittest.TextTestRunner().run(suite)

##################################################
## if run from the command line
if __name__ == '__main__':
    Tests().run()
