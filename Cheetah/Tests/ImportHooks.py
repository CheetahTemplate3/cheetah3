from glob import glob
import os
import shutil
import sys
import unittest
import Cheetah.ImportHooks
from Cheetah.compat import PY2


ImportHooksTemplatesDir = os.path.join(
    os.path.dirname(__file__), 'ImportHooksTemplates')


def setUpModule():
    sys.path.append(ImportHooksTemplatesDir)


def tearDownModule():
    assert sys.path[-1] == ImportHooksTemplatesDir
    del sys.path[-1]


def _cleanup():
    py_files = os.path.join(ImportHooksTemplatesDir, '*.py')
    pyc_files = py_files + 'c'
    for fname in glob(py_files) + glob(pyc_files):
        os.remove(fname)
    __pycache__ = os.path.join(ImportHooksTemplatesDir, '__pycache__')
    if os.path.isdir(__pycache__):
        shutil.rmtree(__pycache__)

    for modname in list(sys.modules.keys()):
        if '.ImportHooksTemplates.' in modname \
                or modname.endswith('.ImportHooksTemplates'):
            del sys.modules[modname]

    for modname in 'index', 'layout':
        if modname in sys.modules:
            del sys.modules[modname]

    Cheetah.ImportHooks.uninstall()


def _exec(code, _dict):
    exec(code, _dict)


class ImportHooksTest(unittest.TestCase):
    def setUp(self):
        _cleanup()

    def tearDown(self):
        _cleanup()

    def test_CheetahDirOwner(self):
        templates = list(sorted(os.listdir(ImportHooksTemplatesDir)))
        self.assertListEqual(templates, ['index.tmpl', 'layout.tmpl'])

        cdo = Cheetah.ImportHooks.CheetahDirOwner(ImportHooksTemplatesDir)
        index_mod = cdo.getmod('index')
        templates = os.listdir(ImportHooksTemplatesDir)
        self.assertIn('index.py', templates)
        self.assertNotIn('layout.py', templates)

        index_co = index_mod.__co__
        del index_mod.__co__
        self.assertRaises(ImportError, _exec, index_co, index_mod.__dict__)

        cdo.getmod('layout')  # Compiled to layout.py and .pyc
        self.assertIn('layout.py', os.listdir(ImportHooksTemplatesDir))

    def test_ImportHooks(self):
        templates = os.listdir(ImportHooksTemplatesDir)
        self.assertNotIn('index.py', templates)
        self.assertNotIn('layout.py', templates)
        Cheetah.ImportHooks.install()
        from index import index  # noqa
        templates = os.listdir(ImportHooksTemplatesDir)
        self.assertIn('index.py', templates)
        self.assertIn('layout.py', templates)

    def test_import_builtin(self):
        Cheetah.ImportHooks.install()
        for nm in sys.builtin_module_names:
            if nm not in sys.modules:
                __import__(nm)
                return
        raise self.fail("All builtin modules are imported")

    if not PY2:
        def test_import_bootlocale(self):
            if '_bootlocale' in sys.modules:
                del sys.modules['_bootlocale']
            Cheetah.ImportHooks.install()
            import _bootlocale  # noqa: F401 '_bootlocale' imported but unused
