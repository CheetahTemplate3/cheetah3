#!/usr/bin/env python
# $Id: Template.py,v 1.106 2002/10/19 23:29:21 hierro Exp $
"""Provides the core Template class for Cheetah
See the docstring in __init__.py and the User's Guide for more information

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@damnsimple.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.106 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2002/10/19 23:29:21 $
""" 
__author__ = "Tavis Rudd <tavis@damnsimple.com>"
__revision__ = "$Revision: 1.106 $"[11:-2]

##################################################
## DEPENDENCIES

import os                         # used to get environ vars, etc.
import sys                        # used in the error handling code
import re                         # used to define the internal delims regex
import new                        # used to bind the compiled template code
import types                      # used in the mergeNewTemplateData method
                                  # and in Template.__init__()
from types import StringType, ClassType
import time                       # used in the cache refresh code
from time import time as currentTime # used in the cache refresh code
import types                      # used in the constructor
import os.path                    # used in Template.normalizePath()
from os.path import getmtime, exists
from random import randrange
from tempfile import mktemp
import imp
import traceback

import __builtin__

# Base classes for Template (intra-package imports)
from SettingsManager import SettingsManager  
from Servlet import Servlet                 
from Cheetah.Utils.WebInputMixin import WebInputMixin

# More intra-package imports ...
import ErrorCatchers              # for placeholder tags
import Filters                          # the output filters
from DummyTransaction import DummyTransaction
from NameMapper import NotFound, valueFromSearchList, valueForName # this is used in the generated code
from Utils import VerifyType             # Used in Template.__init__
from Utils.Misc import checkKeywords     # Used in Template.__init__
from Utils.Indenter import Indenter      # Used in Template.__init__ and for
                                         # placeholders

##################################################
## CONSTANTS & GLOBALS

try:
    True, False
except NameError:
    True, False = (1==1),(1==0)

VFS = valueFromSearchList
VFN = valueForName

##################################################
## CLASSES

class NoDefault:
    pass

class Error(Exception):
    pass
    
class Template(SettingsManager, Servlet, WebInputMixin):
    
    """The core template engine.  It serves as a base class for Template
    servlets and also knows how to compile a template."""

    # All the keyword arguments allowed in the Template constructor.
    _legalKWs = ['_globalSetVars', '_preBuiltSearchList']

    def __init__(self, source=None, searchList=[], file=None,
                 settings={},           # user settings that are visible in templates
                 filter='ReplaceNone', # which filter from Cheetah.Filters
                 filtersLib=Filters,
                 errorCatcher=None,
                 
                 compilerSettings = {}, # control the behaviour of the compiler
                 **KWs        # used internally for #include'd templates
                 ):
        
        """Reads in the template definition, sets up the namespace searchList,
        processes settings, then compiles.

        Configuration settings should be passed in as a dictionary via the
        'settings' keyword.

        This method can also be called without arguments in cases where it is
        called as a baseclass from a pre-compiled Template servlet."""
        
        ##################################################           
        ## Verify argument keywords and types

        checkKeywords(KWs, self._legalKWs, 'Template constructor argument')

        S = types.StringType
        L = types.ListType
        T = types.TupleType
        D = types.DictType
        F = types.FileType
        C = types.ClassType
        M = types.ModuleType
        N = types.NoneType
        vt = VerifyType.VerifyType
        vtc = VerifyType.VerifyTypeClass
        try:
            vt(source, 'source', [N,S], 'string or None')
            vt(searchList, 'searchList', [L,T], 'list or tuple')
            vt(file, 'file', [N,S,F], 'string, file open for reading, or None')
            vt(settings, 'settings', [D], 'dictionary')
            vtc(filter, 'filter', [S,C], 'string or class', 
                Filters.Filter,
                '(if class, must be subclass of Cheetah.Filters.Filter)')
            vt(filtersLib, 'filtersLib', [S,M], 'string or module',
                '(if module, must contain subclasses of Cheetah.Filters.Filter)')
            vtc(errorCatcher, 'errorCatcher', [N,S,C], 'string, class or None',
               ErrorCatchers.ErrorCatcher,
               '(if class, must be subclass of Cheetah.ErrorCatchers.ErrorCatcher)')
            vt(compilerSettings, 'compilerSettings', [D], 'dictionary')
        except TypeError, reason:
            # Re-raise the exception here so that the traceback will end in
            # this function rather than in some utility function.
            raise TypeError(reason)
        
        if source is not None and file is not None:
            raise TypeError("you must supply either a source string or the" + 
                            " 'file' keyword argument, but not both")

        
        ##################################################           
        ## Do superclass initialization.

        SettingsManager.__init__(self)
        Servlet.__init__(self)
        self._compilerSettings = compilerSettings

        ##################################################
        ## Now, compile if we're meant to
        self._cacheIndex = {}
        self._cacheData = {}
        self._generatedModuleCode = None
        self._generatedClassCode = None
        if source or file:
            self.compile(source, file)

        
        ##################################################           
        ## Setup the searchList of namespaces in which to search for $placeholders
        # + setup a dict of #set directive vars - include it in the searchList

        self._globalSetVars = {}

        if KWs.has_key('_globalSetVars'):
            # this is intended to be used internally by Nested Templates in #include's
            self._globalSetVars = KWs['_globalSetVars']
            
        if KWs.has_key('_preBuiltSearchList'):
            # happens with nested Template obj creation from #include's
            self._searchList = list(KWs['_preBuiltSearchList'])
            self._searchList.append(self)
        else:
            # create our own searchList
            self._searchList = [self._globalSetVars]            
            self._searchList.extend(list(searchList))
            self._searchList.append( self )
                
        ##################################################
        ## setup the ouput filters
        self._filtersLib = filtersLib
        self._filters = {}
        if type(filter) == StringType:
            filterName = filter
            klass = getattr(self._filtersLib, filterName)
        else:
            klass = filter
            filterName = klass.__name__
            
        self._currentFilter = self._filters[filterName] = klass(self).filter
        self._initialFilter = self._currentFilter

        ##################################################
        ## setup the errorChecker
        self._errorCatchers = {}
        if errorCatcher:
            if type(errorCatcher) == StringType:
                errorCatcherClass = getattr(ErrorCatchers, errorCatcher)
            elif type(errorCatcher) == ClassType:
                errorCatcherClass = errorCatcher

            self._errorCatcher = self._errorCatchers[errorCatcher.__class__.__name__] = \
                                 errorCatcherClass(self)
        else:
            self._errorCatcher = None
        self._initErrorCatcher = self._errorCatcher
        
        ##################################################
        ## Setup the indenter
        self._indenter = Indenter()
        self._indent = self._indenter.indent
        

            
    def compile(self, source=None, file=None,
                moduleName=None,
                mainMethodName='respond'):
        
        """Compile the template. This method is automatically called by __init__
        when __init__ is fed a file or source string."""
        
        from Compiler import Compiler
        
        if file and type(file) == StringType and not moduleName and \
           re.match(r'[a-zA-Z_][a-zA-Z_0-9]*$', file):
            moduleName = os.path.splitext(os.path.split(file)[1])[0]
        elif not moduleName:
            moduleName='GenTemplate'

        self._fileMtime = None
        self._fileDirName = None
        self._fileBaseName = None
        if file and type(file) == StringType:
            file = self.serverSidePath(file)
            self._fileMtime = os.path.getmtime(file)
            self._fileDirName, self._fileBaseName = os.path.split(file)
        self._filePath = file
                    
        compiler = Compiler(source, file,
                            moduleName=moduleName,
                            mainMethodName=mainMethodName,
                            templateObj=self,
                            settings=self._compilerSettings,
                            )
        compiler.compile()
        self._generatedModuleCode = str(compiler)
        self._generatedClassCode = str(compiler._finishedClassIndex[moduleName])

        compiler._templateObj = None
        compiler.__dict__ = {}
        del compiler

    def generatedModuleCode(self):
        
        """Return the module code the compiler generated, or None if no
        compilation took place."""
        
        return self._generatedModuleCode
    
    def generatedClassCode(self):
        
        """Return the class code the compiler generated, or None if no
        compilation took place."""

        return self._generatedClassCode
    
    def searchList(self):
        """Return a reference to the searchlist"""
        return self._searchList

    def addToSearchList(self, object):
        """Append an object to the end of the searchlist.""" 
        self._searchList.append(object)

    def prependToSearchList(self, object):
        """Prepend an object to the end of the searchlist.""" 
        self._searchList.insert(0, object)

    def errorCatcher(self):
        """Return a reference to the current errorCatcher"""
        return self._errorCatcher

    def refreshCache(self, cacheKey=None):
        
        """Refresh a cache item."""
        
        if not cacheKey:
            self._cacheData.clear()
        else:
            del self._cacheData[ self._cacheIndex[cacheKey] ]
            

    def shutdown(self):
        """Break reference cycles before discarding a servlet."""
        Servlet.shutdown(self)
        self._searchList = None
        self.__dict__ = {}
            
    ## utility functions ##   

    def getVar(self, varName, default=NoDefault, autoCall=True):
        
        """Get a variable from the searchList.  If the variable can't be found
        in the searchList, it returns the default value if one was given, or
        raises NameMapper.NotFound."""
        
        try:
            return VFS(self.searchList(), varName.replace('$',''), autoCall)
        except NotFound:
            if default != NoDefault:
                return default
            else:
                raise
    
    def varExists(self, varName, autoCall=True):
        """Test if a variable name exists in the searchList."""
        try:
            VFS(self.searchList(), varName.replace('$',''), autoCall)
            return True
        except NotFound:
            return False


    hasVar = varExists
    

    def getFileContents(self, path):
        """A hook for getting the contents of a file.  The default
        implementation just uses the Python open() function to load local files.
        This method could be reimplemented to allow reading of remote files via
        various protocols, as PHP allows with its 'URL fopen wrapper'"""
        
        fp = open(path,'r')
        output = fp.read()
        fp.close()
        return output

    
    def runAsMainProgram(self):
        
        """Allows enable the Template to function as a standalone command-line
        program for static page generation.

        Type 'python yourtemplate.py --help to see what it's capabable of.
        """

        from TemplateCmdLineIface import CmdLineIface
        CmdLineIface(templateObj=self).run()
        


    ##################################################
    ## internal methods -- not to be called by end-users

    def _bindCompiledMethod(self, methodCompiler):
        
        """Called by the Compiler class, to add new methods at runtime as the
        compilation process proceeds."""
        
        genCode = str(methodCompiler).strip() + '\n'
        methodName  = methodCompiler.methodName()
        try:
            exec genCode                    # in this namespace!!
        except:
            err = sys.stderr
            print >> err, 'Cheetah was trying to execute the ' + \
                  'following code but Python found a syntax error in it:'
            print >> err
            print >> err,  genCode
            raise
            

        genMeth = self._bindFunctionAsMethod(locals()[methodName])
        
        setattr(self,methodName, genMeth)
        if methodName == 'respond':
            self.__str__ = genMeth

          
    def _bindFunctionAsMethod(self, function):
        """Used to dynamically bind a plain function as a method of the
        Template instance."""
        return new.instancemethod(function, self, self.__class__)


    def _includeCheetahSource(self, srcArg, trans=None, includeFrom='file',
                              raw=False, _includeID=None
                              ):
        
        """This is the method that #include directives translate into."""

        if not hasattr(self, '_cheetahIncludes'):
            self._cheetahIncludes = {}

        if not _includeID:
            _includeID = srcArg
        if not self._cheetahIncludes.has_key(_includeID):
            if includeFrom == 'file':
                path = self.serverSidePath(srcArg)
                if not raw:
                    nestedTemplate = Template(source=None,
                                              file=path,
                                              _preBuiltSearchList=self.searchList(),
                                              _globalSetVars = self._globalSetVars,
                                              )
                    if not hasattr(nestedTemplate, 'respond'):
                        nestedTemplate.compileTemplate()
                    self._cheetahIncludes[_includeID] = nestedTemplate
                else:
                    self._cheetahIncludes[_includeID] = self.getFileContents(path)
            else:                       # from == 'str'
                if not raw:
                    nestedTemplate = Template(
                        source=srcArg,
                        _preBuiltSearchList=self.searchList(),
                        _globalSetVars = self._globalSetVars,
                        )
                    if not hasattr(nestedTemplate, 'respond'):
                        nestedTemplate.compileTemplate()
                    self._cheetahIncludes[_includeID] = nestedTemplate
                else:
                    self._cheetahIncludes[_includeID] = srcArg
        ##

        if not raw:
            self._cheetahIncludes[_includeID].respond(trans)
        else:
            trans.response().write(self._cheetahIncludes[_includeID])


    def _genTmpFilename(self):
        
        """Generate a temporary file name.  This is used internally by the
        Compiler to do correct importing from Cheetah templates when the
        template is compiled via the Template class' interface rather than via
        'cheetah compile'."""
       
        return (
            os.path.split(mktemp())[0] + '/__CheetahTemp_' +
            ''.join(map(lambda x: '%02d' % x, time.localtime(time.time())[:6])) + 
            str(randrange(10000, 99999)) +
            '.py')


    def _importAsDummyModule(self, contents):

        """Used by the Compiler to do correct importing from Cheetah templates
        when the template is compiled via the Template class' interface rather
        than via 'cheetah compile'.
        """
        
        tmpFilename = self._genTmpFilename()
        fp = open(tmpFilename,'w')
        fp.write(contents)
        fp.close()
        if self._filePath:
            moduleDir = self._fileDirName
        else:
            moduleDir = os.getcwd()
            
        packageName = self._makeDummyPackageForDir(moduleDir)
        mod = self._impModFromDummyPackage(packageName, tmpFilename)            
        os.remove(tmpFilename)
        if os.path.exists( tmpFilename + 'c'):
            os.remove(tmpFilename + 'c')
            
        return mod

    def _makeDummyPackageForDir(self, dirName):

        """Returns a Python Package that thinks it came from 'dirName'.
        """
        packageName = 'Cheetah.Temp.' + dirName.replace('\\', '/').replace('/', '_').replace(':','_')
        baseDirName, finalDirName = os.path.split(dirName)
        
        initModulePath = os.path.join(dirName, '__init__.py')
        initModuleExists = False
        if os.path.exists(initModulePath):
            initModuleExists = True            
        
        self._importModuleFromDirectory(
            packageName, finalDirName, baseDirName,
            isPackageDir=1,forceReload=1)
            
        if not initModuleExists and os.path.exists(initModulePath):
            os.remove(initModulePath)
            if os.path.exists(initModulePath + 'c'):
                os.remove(initModulePath + 'c')
        return packageName
        
    def _impModFromDummyPackage(self, packageName, pathToImport):
        
        """Imports a python .py module as if it were part of the package given
        by 'packageName'.  The package doesn't need to exist.
        """
        
        moduleFileName = os.path.basename(pathToImport)
        moduleDir = os.path.dirname(pathToImport)
        moduleName, ext = os.path.splitext(moduleFileName)
        fullModName = packageName + '.' + moduleName
        return self._importModuleFromDirectory(fullModName, moduleName,
                                           moduleDir, forceReload=1)

    def _importModuleFromDirectory(self, fullModuleName, moduleName,
                                   directory, isPackageDir=0, forceReload=0):
        
        """ Imports the given module from the given directory.  fullModuleName
        should be the full dotted name that will be given to the module within
        Python (including the packages, etc.).  moduleName should be the name of
        the module in the filesystem, which may be different from the name given
        in fullModuleName.  Returns the module object.  If forceReload is true
        then this reloads the module even if it has already been imported.
        
        If isPackageDir is true, then this function creates an empty __init__.py
        if that file doesn't already exist.  """
                
        if not forceReload:
            module = sys.modules.get(fullModuleName, None)
            if module is not None:
                return module
        fp = None
        try:
            if isPackageDir:
                # Check if __init__.py is in the directory -- if not, make an empty one.
                packageDir = os.path.join(directory, moduleName)
                initPy = os.path.join(packageDir, '__init__.py')
                if not os.path.exists(initPy):
                    file = open(initPy, 'w')
                    file.write('#')
                    file.close()
            fp, pathname, stuff = imp.find_module(moduleName, [directory])
            module = imp.load_module(fullModuleName, fp, pathname, stuff)
        finally:
            if fp is not None:
                fp.close()
                
        return module


T = Template   # Short and sweet for debugging at the >>> prompt.

# vim: shiftwidth=4 tabstop=4 expandtab
