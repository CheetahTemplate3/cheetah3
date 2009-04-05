#!/usr/bin/env python

import Cheetah.Template
import Cheetah.Filters

import unittest_local_copy as unittest 

class BasicMarkdownFilterTest(unittest.TestCase):
    '''
        Test that our markdown filter works
    '''
    def test_BasicHeader(self):
        template = '''  
#import Cheetah.Filters
#transform Cheetah.Filters.Markdown
$foo

Header
======
        '''
        template = Cheetah.Template.Template(template, searchList=[{'foo' : 'bar'}])
        print template

if __name__ == '__main__':
    unittest.main()
