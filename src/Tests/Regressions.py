#!/usr/bin/env python

import Cheetah.NameMapper 
import Cheetah.Template

import unittest

class GetAttrException(Exception):
    pass

class CustomGetAttrClass(object):
    def __getattr__(self, name):
        raise GetAttrException('FAIL, %s' % name)

class GetAttrTest(unittest.TestCase):
    '''
        Test for an issue occurring when __getatttr__() raises an exception
        causing NameMapper to raise a NotFound exception
    '''
    def test_ValidException(self):
        o = CustomGetAttrClass()
        try:
            print o.attr
        except GetAttrException, e:
            # expected
            return
        except:
            self.fail('Invalid exception raised: %s' % e)
        self.fail('Should have had an exception raised')

    def test_NotFoundException(self):
        template = '''
            #def raiseme()
                $obj.attr
            #end def'''

        template = Cheetah.Template.Template.compile(template, compilerSettings={}, keepRefToGeneratedCode=True)
        template = template(searchList=[{'obj' : CustomGetAttrClass()}])
        assert template, 'We should have a valid template object by now'

        self.failUnlessRaises(GetAttrException, template.raiseme)



if __name__ == '__main__':
    unittest.main()
