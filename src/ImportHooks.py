#!/usr/bin/env python
# $Id: ImportHooks.py,v 1.1 2002/04/18 23:44:37 tavis_rudd Exp $

"""Provides some import hooks to allow Cheetah's .tmpl files to be imported
directly like Python .py modules.

This code is based on Andrew Kuchling's import hooks for Quixote.

Note: there's some unpleasant incompatibility between ZODB's import
trickery and the import hooks here.  Bottom line: if you're using ZODB,
import it *before* installing these import hooks.

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.1 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2002/04/18 23:44:37 $
""" 
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__revision__ = "$Revision: 1.1 $"[11:-2]

##################################################
## DEPENDENCIES

import sys
import os.path
import marshal
import stat
import __builtin__
import imp
import ihooks
import new

# intra-package imports ...
from Compiler import Compiler

##################################################
## CONSTANTS & GLOBALS

try:
    True,False
except NameError:
    True, False = (1==1),(1==0)

TMPL_EXT = '.tmpl'
# Constant used to signal a TMPL files
TMPL_FILE = 129

_installed = False

##################################################
## CLASSES

class CheetahHooks (ihooks.Hooks):

    def get_suffixes (self):
        # add our suffixes
        L = imp.get_suffixes()
        return L + [(TMPL_EXT, 'r', TMPL_FILE)]

class CheetahLoader (ihooks.ModuleLoader):
    
    def load_module (self, name, stuff):
        file, filename, info = stuff
        (suff, mode, type) = info
        if type == TMPL_FILE:
            return self._loadCheetahTemplate(name, filename, file)
        else:
            # Otherwise, use the default handler for loading
            return ihooks.ModuleLoader.load_module( self, name, stuff)
        
    def _loadCheetahTemplate(self, name, filename, file=None):
        if not file:
            try:
                file = open(filename, "r")
            except IOError:
                return None
        path, ext = os.path.splitext(filename)
        basename = os.path.split(path)[1]
        
        ## @@ consider adding an ImportError raiser here
        code = str(Compiler(file=file, moduleName=basename, mainClassName=basename))
        return self._newModule(code, name, filename)

    def _newModule(self, code, name, filename):
        new_mod = new.module(name)
        new_mod.__file__ = filename
        new_mod.__name__ = name
        sys.modules[name] = new_mod
        exec code in new_mod.__dict__
        return new_mod

##################################################
## FUNCTIONS

def install ():
    global _installed
    if not _installed:
        try:
            import ZODB
        except ImportError:
            pass
        hooks = CheetahHooks()
        loader = CheetahLoader(hooks)
        importer = ihooks.ModuleImporter(loader)
        ihooks.install(importer)
        _installed = True

if __name__ == '__main__':
    install()
