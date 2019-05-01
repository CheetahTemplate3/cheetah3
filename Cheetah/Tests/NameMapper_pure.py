import sys
import unittest

try:
    from Cheetah import _namemapper  # noqa
except ImportError:
    # _namemapper hasn't been compiled so Tests/NameMapper.py
    # tests pure-python NameMapper.py; no need to duplicate these tests.
    pass


def _setNameMapperFunctions():
    from Cheetah.NameMapper import NotFound, \
        valueForName, valueFromSearchList, valueFromFrame, \
        valueFromFrameOrSearchList
    from Cheetah.Tests import NameMapper
    for func in [
        NotFound, valueForName, valueFromSearchList,
        valueFromFrame, valueFromFrameOrSearchList
    ]:
        setattr(NameMapper, func.__name__, func)


def setUpModule():
    if 'Cheetah.NameMapper' in sys.modules:
        del sys.modules['Cheetah.NameMapper']
    sys.modules['Cheetah._namemapper'] = None  # emulate absence of the module
    _setNameMapperFunctions()


def tearDownModule():
    del sys.modules['Cheetah.NameMapper']
    del sys.modules['Cheetah._namemapper']
    del sys.modules['Cheetah.Tests.NameMapper']
    _setNameMapperFunctions()  # restore NameMapper


class NameMapperTest(unittest.TestCase):
    def test_valueForName(self):
        from Cheetah.NameMapper import valueForName
        self.assertEqual(valueForName('upper', 'upper', True), 'UPPER')
