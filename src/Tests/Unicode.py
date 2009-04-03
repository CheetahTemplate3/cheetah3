#!/usr/bin/env python
# -*- encoding: utf8 -*-

from Cheetah.Template import Template
from Cheetah import CheetahWrapper
import traceback, tempfile, sys, imp, os
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

        assert t()

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
        assert t().__str__()


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
        t = Template.compile(source="""Main file with |$v| and eacute in the template é""")

        t.v = 'Unicode String'

        assert t()

class JBQ_UTF8_Test5(unittest.TestCase):
    def runTest(self):
        t = Template.compile(source="""#encoding utf-8
        Main file with |$v| and eacute in the template é""")

        t.v = u'Unicode String'
        rc = t().__str__()
        assert rc

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

        assert t()

        sourcefile = tempfile.mktemp()
        f = open("%s.tmpl" % sourcefile, "w")
        f.write(source)
        f.close()
        cw = CheetahWrapper.CheetahWrapper()
        cw.main(["cheetah", "compile", "--nobackup", sourcefile])
        modname = os.path.basename(sourcefile)
        mod = loadModule(modname, ["/tmp"])
        t = eval("mod.%s()" % modname)
        t.v = u'Unicode String'

if __name__ == '__main__':
    unittest.main()
