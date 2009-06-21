import unittest

from Cheetah.Utils import VerifyType
from Cheetah import _verifytype

class VerifyType_Test(unittest.TestCase):
    def test_Verified(self):
        arg = 'foo'
        legalTypes = [str, unicode]
        try:
            rc = VerifyType.VerifyType(arg, 'arg', legalTypes, 'string') 
        except TypeError:
            self.fail('Should not have raised a TypeError here')

        try:
            rc = _verifytype.verifyType(arg, 'arg', legalTypes, 'string')
        except TypeError:
            self.fail('Should not have raised a TypeError here')


if __name__ == '__main__':
    unittest.main()
