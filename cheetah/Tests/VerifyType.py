#!/usr/bin/env python 
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

    def test_IncorrectNumberOfArgs(self):
        arg = 'foo'
        legalTypes = [str, unicode]

        self.failUnlessRaises(TypeError,  VerifyType.VerifyType)
        self.failUnlessRaises(TypeError, _verifytype.verifyType)

        self.failUnlessRaises(TypeError,  VerifyType.VerifyType, arg)
        self.failUnlessRaises(TypeError, _verifytype.verifyType, arg)

        self.failUnlessRaises(TypeError,  VerifyType.VerifyType, arg,
                    'arg')
        self.failUnlessRaises(TypeError, _verifytype.verifyType, arg,
                    'arg')

        self.failUnlessRaises(TypeError,  VerifyType.VerifyType, arg,
                    'arg', legalTypes)
        self.failUnlessRaises(TypeError, _verifytype.verifyType, arg,
                    'arg', legalTypes)

        self.failUnlessRaises(TypeError,  VerifyType.VerifyType, arg,
                    'arg', legalTypes, 'string', 'errmsgExtra', 'one more')
        self.failUnlessRaises(TypeError, _verifytype.verifyType, arg,
                    'arg', legalTypes, 'string', 'errmsgExtra', 'one more')

    def test_LegalTypesNotIterable(self):
        arg = 'foo'
        legalTypes = 1

        self.failUnlessRaises(TypeError,  VerifyType.VerifyType, arg,
                    'arg', legalTypes, 'string')
        self.failUnlessRaises(TypeError, _verifytype.verifyType, arg,
                    'arg', legalTypes, 'string')

class FakeClass(dict):
    pass

class VerifyTypeClass_Test(unittest.TestCase):
    def test_VerifiedClass(self):
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

    def test_UnverifiedClass(self):
        arg = FakeClass
        legalTypes = [type]
        self.failUnlessRaises(TypeError,  VerifyType.VerifyTypeClass, arg,
                    legalTypes, 'subclass of list', list)
        self.failUnlessRaises(TypeError, _verifytype.verifyTypeClass, arg,
                    legalTypes, 'subclass of list', list)

    def test_Verified(self):
        arg = 'foo'
        legalTypes = [str, unicode]
        try:
            rc = VerifyType.VerifyTypeClass(arg, 'arg', legalTypes, 'string', int) 
            assert rc
        except TypeError:
            self.fail('Should not have raised a TypeError here')

        try:
            rc = _verifytype.verifyTypeClass(arg, 'arg', legalTypes, 'string', int)
            assert rc
        except TypeError:
            self.fail('Should not have raised a TypeError here')

    def test_Unverified(self):
        arg = 'foo'
        legalTypes = [list, dict]
        self.failUnlessRaises(TypeError,  VerifyType.VerifyTypeClass, arg,
                    'arg', legalTypes, 'list or dict', int)
        self.failUnlessRaises(TypeError, _verifytype.verifyTypeClass, arg,
                    'arg', legalTypes, 'list or dict', int)

    def test_IncorrectNumberOfArgs(self):
        arg = 'foo'
        legalTypes = [str, unicode]

        self.failUnlessRaises(TypeError,  VerifyType.VerifyTypeClass)
        self.failUnlessRaises(TypeError, _verifytype.verifyTypeClass)

        self.failUnlessRaises(TypeError,  VerifyType.VerifyTypeClass, arg)
        self.failUnlessRaises(TypeError, _verifytype.verifyTypeClass, arg)

        self.failUnlessRaises(TypeError,  VerifyType.VerifyTypeClass, arg,
                    'arg')
        self.failUnlessRaises(TypeError, _verifytype.verifyTypeClass, arg,
                    'arg')

        self.failUnlessRaises(TypeError,  VerifyType.VerifyTypeClass, arg,
                    'arg', legalTypes)
        self.failUnlessRaises(TypeError, _verifytype.verifyTypeClass, arg,
                    'arg', legalTypes)

        self.failUnlessRaises(TypeError,  VerifyType.VerifyTypeClass, arg,
                    'arg', legalTypes, 'string')
        self.failUnlessRaises(TypeError, _verifytype.verifyTypeClass, arg,
                    'arg', legalTypes, 'string')

        self.failUnlessRaises(TypeError,  VerifyType.VerifyTypeClass, arg,
                    'arg', legalTypes, 'string', int, 'errmsgExtra', 'one more')
        self.failUnlessRaises(TypeError, _verifytype.verifyTypeClass, arg,
                    'arg', legalTypes, 'string', int, 'errmsgExtra', 'one more')

    def test_LegalTypesNotIterable(self):
        arg = 'foo'
        legalTypes = 1

        self.failUnlessRaises(TypeError,  VerifyType.VerifyTypeClass, arg,
                    'arg', legalTypes, 'string', int)
        self.failUnlessRaises(TypeError, _verifytype.verifyTypeClass, arg,
                    'arg', legalTypes, 'string', int)




if __name__ == '__main__':
    unittest.main()
