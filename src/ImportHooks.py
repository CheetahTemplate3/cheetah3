#!/usr/bin/env python
# $Id: ImportHooks.py,v 1.4 2002/04/27 01:37:26 tavis_rudd Exp $

"""Provides some import hooks to allow Cheetah's .tmpl files to be imported
directly like Python .py modules.

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@damnsimple.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.4 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2002/04/27 01:37:26 $
""" 
__author__ = "Tavis Rudd <tavis@damnsimple.com>"
__revision__ = "$Revision: 1.4 $"[11:-2]

##################################################
## DEPENDENCIES

import sys
import os.path
import types
import __builtin__
import new
import imp
import ImportManager
from ImportManager import DirOwner
# intra-package imports ...
from Compiler import Compiler

##################################################
## CONSTANTS & GLOBALS

try:
    True,False
except NameError:
    True, False = (1==1),(1==0)

_installed = False

##################################################
## CLASSES

class CheetahDirOwner(DirOwner):

    def getmod(self, name,
               pathIsDir=os.path.isdir,
               newmod=imp.new_module):
               
        tmplPath =  os.path.join(self.path, name + '.tmpl')
        mod = DirOwner.getmod(self, name)
        if mod:
            return mod
        elif not os.path.exists(tmplPath):
            return None
        else:
            ## @@ consider adding an ImportError raiser here
            code = str(Compiler(file=tmplPath, moduleName=name, mainClassName=name))
            mod = new.module(name)
            mod.__file__ = tmplPath
            mod.__name__ = name
            sys.modules[name] = mod
            exec code in mod.__dict__
            ##print name, tmplPath, new_mod
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
