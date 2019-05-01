#!/usr/bin/env python
"""
Core module of Cheetah's Unit-testing framework

TODO
================================================================================
# combo tests
# negative test cases for expected exceptions
# black-box vs clear-box testing
# do some tests that run the Template for long enough to check
# that the refresh code works
"""

import sys
import unittest

from Cheetah.Tests import Analyzer
from Cheetah.Tests import CheetahWrapper
from Cheetah.Tests import Filters
from Cheetah.Tests import ImportHooks
from Cheetah.Tests import LoadTemplate
from Cheetah.Tests import Misc
from Cheetah.Tests import NameMapper
from Cheetah.Tests import NameMapper_pure
from Cheetah.Tests import Parser
from Cheetah.Tests import Regressions
from Cheetah.Tests import SyntaxAndOutput
from Cheetah.Tests import Template
from Cheetah.Tests import TemplateCmdLineIface
from Cheetah.Tests import Unicode

SyntaxAndOutput.install_eols()

suites = [
    unittest.findTestCases(Analyzer),
    unittest.findTestCases(Filters),
    unittest.findTestCases(ImportHooks),
    unittest.findTestCases(LoadTemplate),
    unittest.findTestCases(Misc),
    unittest.findTestCases(NameMapper),
    unittest.findTestCases(Parser),
    unittest.findTestCases(Regressions),
    unittest.findTestCases(SyntaxAndOutput),
    unittest.findTestCases(Template),
    unittest.findTestCases(TemplateCmdLineIface),
    unittest.findTestCases(Unicode),
    unittest.findTestCases(NameMapper_pure),
]

if not sys.platform.startswith('java'):
    suites.append(unittest.findTestCases(CheetahWrapper))

if __name__ == '__main__':
    if 'xml' in sys.argv:
        from Cheetah.Tests import xmlrunner
        runner = xmlrunner.XMLTestRunner(filename='Cheetah-Tests.xml')
    else:
        runner = unittest.TextTestRunner()

    results = runner.run(unittest.TestSuite(suites))
    if results.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)
