#!/usr/bin/env python
# -*- encoding: utf8 -*-

from Cheetah.Template import Template
from Cheetah import CheetahWrapper
import traceback, tempfile, sys, imp, os
import pdb
import unittest_local_copy as unittest # This is stupid

class JBQ_UTF8_Test1(unittest.TestCase):
    def runTest(self):
        t = Template.compile(source="""Main file with |$v|

        $other""")

        otherT = Template.compile(source="Other template with |$v|")
        other = otherT()
        t.other = other

        t.v = u'Unicode String'
        t.other.v = u'Unicode String'

        assert unicode(t())

class JBQ_UTF8_Test2(unittest.TestCase):
    def runTest(self):
        t = Template.compile(source="""Main file with |$v|

        $other""")

        otherT = Template.compile(source="Other template with |$v|")
        other = otherT()
        t.other = other

        t.v = u'Unicode String with eacute é'
        t.other.v = u'Unicode String'

        assert unicode(t())


class JBQ_UTF8_Test3(unittest.TestCase):
    def runTest(self):
        t = Template.compile(source="""Main file with |$v|

        $other""")

        otherT = Template.compile(source="Other template with |$v|")
        other = otherT()
        t.other = other

        t.v = u'Unicode String with eacute é'
        t.other.v = u'Unicode String and an eacute é'

        assert unicode(t())

class JBQ_UTF8_Test4(unittest.TestCase):
    def runTest(self):
        t = Template.compile(source="""#encoding utf-8
        Main file with |$v| and eacute in the template é""")

        t.v = 'Unicode String'

        assert unicode(t())

class JBQ_UTF8_Test5(unittest.TestCase):
    def runTest(self):
        t = Template.compile(source="""#encoding utf-8
        Main file with |$v| and eacute in the template é""")

        t.v = u'Unicode String'

        assert unicode(t())

def loadModule(moduleName, path=None):
    if path:
        assert isinstance(path, list)
    try:
        mod = sys.modules[moduleName]
    except KeyError:
        fp = None

        try:
            fp, pathname, description = imp.find_module(moduleName, path)
            mod = imp.load_module(moduleName, fp, pathname, description)
        finally:
            if fp:
                fp.close()
    return mod

class JBQ_UTF8_Test6(unittest.TestCase):
    def runTest(self):
        source = """#encoding utf-8
        #set $someUnicodeString = u"Bébé"
        Main file with |$v| and eacute in the template é"""
        t = Template.compile(source=source)

        t.v = u'Unicode String'

        assert unicode(t())

class JBQ_UTF8_Test7(unittest.TestCase):
    def runTest(self):
        source = """#encoding utf-8
        #set $someUnicodeString = u"Bébé"
        Main file with |$v| and eacute in the template é"""

        sourcefile = tempfile.mktemp()
        f = open("%s.tmpl" % sourcefile, "w")
        f.write(source)
        f.close()
        cw = CheetahWrapper.CheetahWrapper()
        cw.main(["cheetah", "compile", "--nobackup", sourcefile])
        modname = os.path.basename(sourcefile)
        mod = loadModule(modname, ["/tmp"])
        t = eval("mod.%s" % modname)
        t.v = u'Unicode String'

        assert unicode(t())

class Unicode_in_SearchList_Test(unittest.TestCase):
    def createAndCompile(self, source):
        sourcefile = tempfile.mktemp()
        fd = open('%s.tmpl' % sourcefile, 'w')
        fd.write(source)
        fd.close()

        wrap = CheetahWrapper.CheetahWrapper()
        wrap.main(['cheetah', 'compile', '--nobackup', sourcefile])
        module_name = os.path.basename(sourcefile)
        module = loadModule(module_name, ['/tmp'])
        template = getattr(module, module_name)
        return template

    def test_BasicASCII(self):
        source = '''This is $adjective'''

        template = self.createAndCompile(source)
        assert template and issubclass(template, Template)
        template = template(searchList=[{'adjective' : u'neat'}])
        assert template.respond()

    def test_Thai(self):
        # The string is something in Thai
        source = '''This is $foo $adjective'''
        template = self.createAndCompile(source)
        assert template and issubclass(template, Template)
        template = template(searchList=[{'foo' : 'bar', 
            'adjective' : u'\u0e22\u0e34\u0e19\u0e14\u0e35\u0e15\u0e49\u0e2d\u0e19\u0e23\u0e31\u0e1a'}])
        assert template.respond()


if __name__ == '__main__':
    unittest.main()
