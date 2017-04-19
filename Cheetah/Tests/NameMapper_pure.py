#!/usr/bin/env python

import sys
import unittest

try:
    from Cheetah import _namemapper
except ImportError:
    # _namemapper hasn't been compiled so Tests/NameMapper.py
    # tests pure-python NameMapper.py; no need to duplicate these tests.
    pass
else:  # Test NameMapper tests without _namemapper extension.
    from Cheetah.Tests.NameMapper import *

def setUpModule():
    sys.modules['Cheetah._namemapper'] = None

def tearDownModule():
    del sys.modules['Cheetah._namemapper']

class NameMapperTest(unittest.TestCase):
    def test_valueForName(self):
        from Cheetah.NameMapper import valueForName
        self.assertEqual(valueForName('upper', 'upper', True), 'UPPER')

if __name__ == '__main__':
    unittest.main()
