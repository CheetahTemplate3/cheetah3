#!/usr/bin/env python
'''
Core module of Cheetah's Unit-testing framework

TODO
================================================================================
# combo tests
# negative test cases for expected exceptions
# black-box vs clear-box testing
# do some tests that run the Template for long enough to check that the refresh code works
'''

import sys
import unittest

import SyntaxAndOutput
import NameMapper
import Filters
import Template
import Cheps
import Regressions
import Unicode
import CheetahWrapper

SyntaxAndOutput.install_eols()

suites = [
   unittest.findTestCases(SyntaxAndOutput),
   unittest.findTestCases(NameMapper),
   unittest.findTestCases(Filters),
   unittest.findTestCases(Template),
   #unittest.findTestCases(Cheps),
   unittest.findTestCases(Regressions),
   unittest.findTestCases(Unicode),
]

if not sys.platform.startswith('java'):
    suites.append(unittest.findTestCases(CheetahWrapper))

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    if 'xml' in sys.argv:
        import xmlrunner
        runner = xmlrunner.XMLTestRunner(filename='Cheetah-Tests.xml')
    
    results = runner.run(unittest.TestSuite(suites))

