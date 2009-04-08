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
#from Cheetah.Filters import Markdown
#transform Markdown
$foo

Header
======
        '''
        expected = '''<p>bar</p>
<h1>Header</h1>'''
        template = Cheetah.Template.Template(template, searchList=[{'foo' : 'bar'}])
        template = str(template)
        assert template == expected

class BasicCodeHighlighterFilterTest(unittest.TestCase):
    '''
        Test that our code highlighter filter works
    '''
    def test_Python(self):
        template = '''  
#from Cheetah.Filters import CodeHighlighter
#transform CodeHighlighter

def foo(self):
    return '$foo'
        '''
        template = Cheetah.Template.Template(template, searchList=[{'foo' : 'bar'}])
        template = str(template)
        assert template, (template, 'We should have some content here...')

    def test_Html(self):
        template = '''  
#from Cheetah.Filters import CodeHighlighter
#transform CodeHighlighter

<html><head></head><body>$foo</body></html>
        '''
        template = Cheetah.Template.Template(template, searchList=[{'foo' : 'bar'}])
        template = str(template)
        assert template, (template, 'We should have some content here...')


if __name__ == '__main__':
    unittest.main()
