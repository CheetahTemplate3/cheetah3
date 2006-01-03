#!/usr/bin/env python
# $Id: ImportHooks.py,v 1.23 2006/01/03 19:33:08 tavis_rudd Exp $

"""Provides some import hooks to allow Cheetah's .tmpl files to be imported
directly like Python .py modules.

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@damnsimple.com>
License: This software is released for unlimited distribution under the
         terms of the MIT license.  See the LICENSE file.
Version: $Revision: 1.23 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2006/01/03 19:33:08 $
""" 
__author__ = "Tavis Rudd <tavis@damnsimple.com>"
__revision__ = "$Revision: 1.23 $"[11:-2]

import sys
import os.path
import types
import __builtin__
import new
import imp
from threading import Lock
import string
import traceback
from Cheetah import ImportManager
from Cheetah.ImportManager import DirOwner
from Cheetah.Compiler import Compiler
from Cheetah.convertTmplPathToModuleName import convertTmplPathToModuleName

_installed = False

##################################################
## HELPER FUNCS

_cacheDir = []
def setCacheDir(cacheDir):
    global _cacheDir
    _cacheDir.append(cacheDir)
    
##################################################
## CLASSES

class CheetahDirOwner(DirOwner):
    _lock = Lock()
    _acquireLock = _lock.acquire
    _releaseLock = _lock.release
    

    def getmod(self, name,
               pathIsDir=os.path.isdir,
               join=os.path.join,
               newmod=imp.new_module,
               convertTmplPath=convertTmplPathToModuleName,
               ):
        
        tmplPath =  os.path.join(self.path, name + '.tmpl')
        mod = DirOwner.getmod(self, name)
        if mod:
            return mod
        elif not os.path.exists(tmplPath):
            return None
        else:
            self._acquireLock()
            try:
                try:
                    return self._compile(name, tmplPath)
                except:
                    # @@TR: log the error
                    exc_txt = traceback.format_exc()
                    exc_txt ='  '+('  \n'.join(exc_txt.splitlines()))
                    raise ImportError(
                        'Error while compiling Cheetah module'
                        ' %(name)s, original traceback follows:\n%(exc_txt)s'%locals())
            finally:
                self._releaseLock()          

    def _compile(self, name, tmplPath):
        ## @@ consider adding an ImportError raiser here
        code = str(Compiler(file=tmplPath, moduleName=name,
                            mainClassName=name))
        if _cacheDir:
            __file__ = join(_cacheDir[0], convertTmplPath(tmplPath)) + '.py'
            try:
                open(__file__, 'w').write(code)
            except OSError:
                ## @@ TR: need to add some error code here
                traceback.print_exc(file=sys.stderr)
                __file__ = tmplPath
        else:
            __file__ = tmplPath
        co = compile(code+'\n', __file__, 'exec')

        mod = newmod(name)
        mod.__file__ = co.co_filename
        if _cacheDir:
            mod.__orig_file__ = tmplPath # @@TR: this is used in the WebKit
                                         # filemonitoring code
        mod.__co__ = co
        return mod
        

##################################################
## FUNCTIONS

def install():
    """Install the Cheetah Import Hooks"""
    global _installed
    if not _installed:
        import __builtin__
        if type(__builtin__.__import__) == types.BuiltinFunctionType:
            global __oldimport__
            __oldimport__ = __builtin__.__import__
            ImportManager._globalOwnerTypes.insert(0, CheetahDirOwner)
            #ImportManager._globalOwnerTypes.append(CheetahDirOwner)            
            global _manager
            _manager=ImportManager.ImportManager()
            _manager.setThreaded()
            _manager.install()
        
def uninstall():
    """Uninstall the Cheetah Import Hooks"""    
    global _installed
    if not _installed:
        import __builtin__
        if type(__builtin__.__import__) == types.MethodType:
            __builtin__.__import__ = __oldimport__
            global _manager
            del _manager

if __name__ == '__main__':
    install()
