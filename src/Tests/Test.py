#!/usr/bin/env python
# $Id: Test.py,v 1.27 2001/10/10 06:57:22 tavis_rudd Exp $
"""Unit-testing framework for the Cheetah package

TODO
================================================================================
- Check NameMapper independently

# combo tests
# negative test cases for expected exceptions
# black-box vs clear-box testing
# do some tests that run the Template for long enough to check that the refresh code works

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>,
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.27 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2001/10/10 06:57:22 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.27 $"[11:-2]


##################################################
## DEPENDENCIES ##

import sys
import unittest_local_copy as unittest

##################################################
## CONSTANTS & GLOBALS

True = (1==1)
False = (0==1)

##################################################
## if run from the command line
if __name__ == '__main__':
    import SyntaxAndOutput, NameMapper, Template
    
    suite = unittest.findTestCases(SyntaxAndOutput)
    suite.addTest( unittest.findTestCases(NameMapper) )
    suite.addTest( unittest.findTestCases(Template) )
    
    unittest.TextTestRunner().run(suite)
