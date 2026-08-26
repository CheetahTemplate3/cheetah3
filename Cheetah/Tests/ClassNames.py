'''
Tests for the ``titleCaseClassNames`` compiler setting.
'''

import os
import shutil
import sys
import tempfile
import unittest

from Cheetah.Compiler import ModuleCompiler, titleCaseClassName
from Cheetah.LoadTemplate import loadTemplateClass
from Cheetah.Template import Template


def compileToSource(source, **kw):
    """Compile a template and return the generated Python source as text"""
    pysrc = Template.compile(source, returnAClass=False, **kw)
    if not isinstance(pysrc, str):
        pysrc = pysrc.decode('utf-8')
    return pysrc


class TitleCaseClassNameTest(unittest.TestCase):

    def test_underscores(self):
        self.assertEqual(titleCaseClassName('my_template'), 'MyTemplate')
        self.assertEqual(titleCaseClassName('my__template'), 'MyTemplate')
        self.assertEqual(titleCaseClassName('my_2nd_template'),
                         'My2ndTemplate')

    def test_single_word(self):
        self.assertEqual(titleCaseClassName('template'), 'Template')

    def test_already_title_case(self):
        self.assertEqual(titleCaseClassName('MyTemplate'), 'MyTemplate')
        self.assertEqual(titleCaseClassName('HTMLPage'), 'HTMLPage')

    def test_leading_underscores(self):
        self.assertEqual(titleCaseClassName('_my_template'), '_MyTemplate')
        self.assertEqual(titleCaseClassName('__my_template'), '__MyTemplate')

    def test_keywords(self):
        # class None(Template) is a syntax error.
        self.assertEqual(titleCaseClassName('none'), 'None_')
        self.assertEqual(titleCaseClassName('true'), 'True_')
        self.assertEqual(titleCaseClassName('lambda'), 'Lambda')


class CompileTest(unittest.TestCase):

    def compile(self, source, moduleName='my_template', **settings):
        return compileToSource(source, moduleName=moduleName,
                               compilerSettings=settings)


class ClassNameTest(CompileTest):

    def test_off_by_default(self):
        pysrc = self.compile('Hello')
        self.assertIn('class my_template(', pysrc)

    def test_title_case(self):
        pysrc = self.compile('Hello', titleCaseClassNames=True)
        self.assertIn('class MyTemplate(', pysrc)

    def test_returns_the_compiled_class(self):
        klass = Template.compile(
            'Hello', moduleName='my_template',
            compilerSettings={'titleCaseClassNames': True})
        self.assertEqual(klass.__name__, 'MyTemplate')
        self.assertEqual(str(klass()), 'Hello')

    def test_setting_on_a_template_subclass(self):
        class TitleCased(Template):
            _CHEETAH_compilerSettings = {'titleCaseClassNames': True}

        klass = TitleCased.compile('Hello', moduleName='my_template')
        self.assertEqual(klass.__name__, 'MyTemplate')
        self.assertEqual(str(klass()), 'Hello')

    def test_compiler_settings_directive_does_not_apply(self):
        # The class name is fixed before parsing starts, so the directive
        # comes too late. It must not rename half of the module either.
        pysrc = self.compile("""\
#compiler-settings
titleCaseClassNames = True
#end compiler-settings
#extends my_base
#implements respond
Hello
""")
        self.assertIn('from my_base import my_base', pysrc)
        self.assertIn('class my_template(my_base)', pysrc)

    def test_explicit_class_name(self):
        pysrc = compileToSource(
            'Hello', moduleName='my_template', className='other_name',
            compilerSettings={'titleCaseClassNames': True})
        self.assertIn('class OtherName(', pysrc)


class ExtendsTest(CompileTest):

    baseTemplate = """\
#extends my_base
#implements respond
Hello
"""

    def test_off_by_default(self):
        pysrc = self.compile(self.baseTemplate)
        self.assertIn('from my_base import my_base', pysrc)
        self.assertIn('class my_template(my_base)', pysrc)

    def test_title_case(self):
        pysrc = self.compile(self.baseTemplate, titleCaseClassNames=True)
        self.assertIn('from my_base import MyBase', pysrc)
        self.assertIn('class MyTemplate(MyBase)', pysrc)

    def test_title_case_dotted(self):
        pysrc = self.compile("""\
#extends templates.my_base
#implements respond
Hello
""", titleCaseClassNames=True)
        self.assertIn('from templates.my_base import MyBase', pysrc)
        self.assertIn('class MyTemplate(MyBase)', pysrc)

    def test_title_case_module_named_after_its_class(self):
        pysrc = self.compile("""\
#extends my_base.my_base
#implements respond
Hello
""", titleCaseClassNames=True)
        self.assertIn('from my_base import MyBase', pysrc)
        self.assertIn('class MyTemplate(MyBase)', pysrc)

    def test_explicit_class_name_is_kept(self):
        # The last chunk names a class, not a module, so it is left alone.
        pysrc = self.compile("""\
#extends Cheetah.Templates.SkeletonPage.SkeletonPage
#implements respond
Hello
""", titleCaseClassNames=True)
        self.assertIn(
            'from Cheetah.Templates.SkeletonPage import SkeletonPage', pysrc)

    def test_imported_class_name_is_kept(self):
        pysrc = self.compile("""\
#from Cheetah.Templates.SkeletonPage import SkeletonPage
#extends SkeletonPage
#implements respond
Hello
""", titleCaseClassNames=True)
        self.assertIn('class MyTemplate(SkeletonPage)', pysrc)


class InheritanceTest(unittest.TestCase):
    """Compile a base and a derived template and run the derived one."""

    settings = {'titleCaseClassNames': True}

    moduleNames = ('inherit_base', 'inherit_template')

    def setUp(self):
        self.tmpDir = tempfile.mkdtemp()
        sys.path.insert(0, self.tmpDir)
        self.dropModules()

    def tearDown(self):
        sys.path.remove(self.tmpDir)
        self.dropModules()
        shutil.rmtree(self.tmpDir, ignore_errors=True)

    def dropModules(self):
        for moduleName in self.moduleNames:
            sys.modules.pop(moduleName, None)

    def writeTemplate(self, moduleName, source):
        pysrc = compileToSource(
            source, moduleName=moduleName, className=moduleName,
            compilerSettings=self.settings)
        pyFile = open(os.path.join(self.tmpDir, moduleName + '.py'), 'w')
        try:
            pyFile.write(pysrc)
        finally:
            pyFile.close()

    def test_inheritance(self):
        self.writeTemplate('inherit_base', """\
#def greet
Hello from the base
#end def
""")
        self.writeTemplate('inherit_template', """\
#extends inherit_base
#implements respond
$greet()""")
        from inherit_template import InheritTemplate
        self.assertEqual(str(InheritTemplate()), 'Hello from the base\n')


class KeywordClassNameTest(unittest.TestCase):

    def test_compiles_and_runs(self):
        klass = Template.compile(
            'Hello', moduleName='none',
            compilerSettings={'titleCaseClassNames': True})
        self.assertEqual(klass.__name__, 'None_')
        self.assertEqual(str(klass()), 'Hello')


class CustomCompilerClassTest(unittest.TestCase):
    """A compilerClass of one's own need not know about the setting"""

    class PlainCompiler(object):
        def __init__(self, *args, **kw):
            self._compiler = ModuleCompiler(*args, **kw)

        def compile(self):
            return self._compiler.compile()

        def getModuleCode(self):
            return self._compiler.getModuleCode()

        def getModuleEncoding(self):
            return self._compiler.getModuleEncoding()

    def test_compiles(self):
        klass = Template.compile('Hello', moduleName='plain_template',
                                 compilerClass=self.PlainCompiler)
        self.assertEqual(klass.__name__, 'plain_template')
        self.assertEqual(str(klass()), 'Hello')


class LoadTemplateClassTest(unittest.TestCase):

    moduleName = 'loaded_template'

    def setUp(self):
        self.tmpDir = tempfile.mkdtemp()
        sys.modules.pop(self.moduleName, None)

    def tearDown(self):
        sys.modules.pop(self.moduleName, None)
        shutil.rmtree(self.tmpDir, ignore_errors=True)

    def test_loads_a_title_cased_class(self):
        pysrc = compileToSource(
            'Hello', moduleName=self.moduleName, className=self.moduleName,
            compilerSettings={'titleCaseClassNames': True})
        pyFile = open(
            os.path.join(self.tmpDir, self.moduleName + '.py'), 'w')
        try:
            pyFile.write(pysrc)
        finally:
            pyFile.close()
        klass = loadTemplateClass(
            os.path.join(self.tmpDir, self.moduleName))
        self.assertEqual(klass.__name__, 'LoadedTemplate')
        self.assertEqual(str(klass()), 'Hello')


if __name__ == '__main__':
    unittest.main()
