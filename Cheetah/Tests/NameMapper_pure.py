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
    if 'Cheetah.NameMapper' in sys.modules:
        del sys.modules['Cheetah.NameMapper']
    sys.modules['Cheetah._namemapper'] = None
    from Cheetah.NameMapper import NotFound, valueForKey, \
         valueForName, valueFromSearchList, valueFromFrame, \
         valueFromFrameOrSearchList
    from Cheetah.Tests import NameMapper
    for func in [
        NotFound, valueForKey, valueForName, valueFromSearchList,
        valueFromFrame, valueFromFrameOrSearchList
    ]:
        setattr(NameMapper, func.__name__, func)

def tearDownModule():
    del sys.modules['Cheetah.NameMapper']
    del sys.modules['Cheetah._namemapper']
    del sys.modules['Cheetah.Tests.NameMapper']

class NameMapperTest(unittest.TestCase):
    def test_valueForName(self):
        from Cheetah.NameMapper import valueForName
        self.assertEqual(valueForName('upper', 'upper', True), 'UPPER')

if __name__ == '__main__':
    unittest.main()
