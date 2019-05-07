"""
Provides some import hooks to allow Cheetah's .tmpl files to be imported
directly like Python .py modules.

To use these:
  import Cheetah.ImportHooks
  Cheetah.ImportHooks.install()
"""

try:
    from importlib import invalidate_caches
except ImportError:
    invalidate_caches = None
import sys
import os.path
import py_compile
import types
try:
    import builtins as builtin
except ImportError:  # PY2
    import __builtin__ as builtin
from threading import RLock
import traceback

from Cheetah import ImportManager
from Cheetah.ImportManager import DirOwner
from Cheetah.Compiler import Compiler
from Cheetah.convertTmplPathToModuleName import convertTmplPathToModuleName

_installed = False

##################################################
# HELPER FUNCS

_cacheDir = []


def setCacheDir(cacheDir):
    global _cacheDir
    _cacheDir.append(cacheDir)

##################################################
# CLASSES


class CheetahDirOwner(DirOwner):
    _lock = RLock()
    _acquireLock = _lock.acquire
    _releaseLock = _lock.release

    templateFileExtensions = ('.tmpl',)
    debuglevel = 0

    def getmod(self, name):
        self._acquireLock()
        try:
            mod = DirOwner.getmod(self, name)
            if mod:
                return mod

            for ext in self.templateFileExtensions:
                tmplPath = os.path.join(self.path, name + ext)
                if os.path.exists(tmplPath):
                    try:
                        return self._compile(name, tmplPath)
                    except Exception:
                        # @@TR: log the error
                        exc_txt = traceback.format_exc()
                        exc_txt = '  ' + ('  \n'.join(exc_txt.splitlines()))
                        raise ImportError(
                            'Error while compiling Cheetah module '
                            '%(name)s, original traceback follows:\n'
                            '%(exc_txt)s' % locals())
            return None

        finally:
            self._releaseLock()

    def _compile(self, name, tmplPath):
        if invalidate_caches:
            invalidate_caches()

        # @@ consider adding an ImportError raiser here
        code = str(Compiler(file=tmplPath, moduleName=name,
                            mainClassName=name))
        if _cacheDir:
            __file__ = os.path.join(
                _cacheDir[0], convertTmplPathToModuleName(tmplPath)) + '.py'
        else:
            __file__ = os.path.splitext(tmplPath)[0] + '.py'
        try:
            with open(__file__, 'w') as _py_file:
                _py_file.write(code)
        except (IOError, OSError):
            # @@ TR: need to add some error code here
            if self.debuglevel > 0:
                traceback.print_exc(file=sys.stderr)
            __file__ = tmplPath
        else:
            try:
                py_compile.compile(__file__)
            except IOError:
                pass
        co = compile(code + '\n', __file__, 'exec')

        mod = types.ModuleType(name)
        mod.__file__ = co.co_filename
        if _cacheDir:
            # @@TR: this is used in the WebKit filemonitoring code
            mod.__orig_file__ = tmplPath
        mod.__co__ = co
        return mod


##################################################
# FUNCTIONS

def install(templateFileExtensions=('.tmpl',)):
    """Install the Cheetah Import Hooks"""

    global _installed
    if not _installed:
        CheetahDirOwner.templateFileExtensions = templateFileExtensions
        if isinstance(builtin.__import__, types.BuiltinFunctionType):
            global __oldimport__
            ImportManager.__oldimport__ = __oldimport__ = builtin.__import__
            ImportManager._globalOwnerTypes.insert(0, CheetahDirOwner)
            global _manager
            _manager = ImportManager.ImportManager()
            _manager.setThreaded()
            _manager.install()
            _installed = True


def uninstall():
    """Uninstall the Cheetah Import Hooks"""
    global _installed
    if _installed:
        if isinstance(builtin.__import__, types.MethodType):
            builtin.__import__ = __oldimport__
            if ImportManager._globalOwnerTypes[0] is CheetahDirOwner:
                del ImportManager._globalOwnerTypes[0]
            del ImportManager.__oldimport__
            global _manager
            del _manager
            _installed = False
