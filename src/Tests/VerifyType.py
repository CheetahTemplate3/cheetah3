import unittest

from Cheetah.Utils import VerifyType
from Cheetah import _verifytype

class VerifyType_Test(unittest.TestCase):
    def test_Verified(self):
        arg = 'foo'
        legalTypes = [str, unicode]
        try:
            rc = VerifyType.VerifyType(arg, 'arg', legalTypes, 'string') 
            assert rc
        except TypeError:
            self.fail('Should not have raised a TypeError here')

        try:
            rc = _verifytype.verifyType(arg, 'arg', legalTypes, 'string')
            assert rc
        except TypeError:
            self.fail('Should not have raised a TypeError here')

    def test_Unverified(self):
        arg = 'foo'
        legalTypes = [list, dict]
        self.failUnlessRaises(TypeError, VerifyType.VerifyType, arg,
                    'arg', legalTypes, 'list or dict')
        self.failUnlessRaises(TypeError, _verifytype.verifyType, arg,
                    'arg', legalTypes, 'list or dict')

class FakeClass(dict):
    pass

class VerifyTypeClass_Test(unittest.TestCase):
    def test_Verified(self):
        arg = FakeClass
        legalTypes = [type]
        try:
            rc = VerifyType.VerifyTypeClass(arg, 'arg', legalTypes, '', dict) 
            assert rc
        except TypeError:
            self.fail('Should not have raised a TypeError here')

        try:
            rc = _verifytype.verifyTypeClass(arg, 'arg', legalTypes, 'foo', dict)
            assert rc
        except TypeError:
            self.fail('Should not have raised a TypeError here')




if __name__ == '__main__':
    unittest.main()
