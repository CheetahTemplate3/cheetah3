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

args_l = len(sys.argv)
if args_l == 1:
    pass
elif args_l == 2 and sys.argv[1] == '--namemapper-pure':
    try:
        from Cheetah import _namemapper  # noqa
    except ImportError:
        # _namemapper hasn't been compiled so Tests/NameMapper.py
        # tests pure-python NameMapper.py; no need to duplicate these tests.
        print('Ok')
        sys.exit(0)
    sys.modules['Cheetah._namemapper'] = None
    sys._cheetah_namemapper_pure = True
else:
    sys.exit('Wrong argument or wrong number of arguments')

import unittest  # noqa: E402 module level import not at top of file

from Cheetah.Tests import Analyzer  # noqa: E402
from Cheetah.Tests import CheetahWrapper  # noqa: E402
from Cheetah.Tests import Filters  # noqa: E402
from Cheetah.Tests import ImportHooks  # noqa: E402
from Cheetah.Tests import LoadTemplate  # noqa: E402
from Cheetah.Tests import Misc  # noqa: E402
from Cheetah.Tests import NameMapper  # noqa: E402
from Cheetah.Tests import Parser  # noqa: E402
from Cheetah.Tests import Regressions  # noqa: E402
from Cheetah.Tests import SyntaxAndOutput  # noqa: E402
from Cheetah.Tests import Template  # noqa: E402
from Cheetah.Tests import TemplateCmdLineIface  # noqa: E402
from Cheetah.Tests import Unicode  # noqa: E402

SyntaxAndOutput.install_eols()

suites = [
    unittest.defaultTestLoader.loadTestsFromModule(Analyzer),
    unittest.defaultTestLoader.loadTestsFromModule(Filters),
    unittest.defaultTestLoader.loadTestsFromModule(ImportHooks),
    unittest.defaultTestLoader.loadTestsFromModule(LoadTemplate),
    unittest.defaultTestLoader.loadTestsFromModule(Misc),
    unittest.defaultTestLoader.loadTestsFromModule(NameMapper),
    unittest.defaultTestLoader.loadTestsFromModule(Parser),
    unittest.defaultTestLoader.loadTestsFromModule(Regressions),
    unittest.defaultTestLoader.loadTestsFromModule(SyntaxAndOutput),
    unittest.defaultTestLoader.loadTestsFromModule(Template),
    unittest.defaultTestLoader.loadTestsFromModule(TemplateCmdLineIface),
    unittest.defaultTestLoader.loadTestsFromModule(Unicode),
]

if not sys.platform.startswith('java'):
    suites.append(
        unittest.defaultTestLoader.loadTestsFromModule(CheetahWrapper))

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
