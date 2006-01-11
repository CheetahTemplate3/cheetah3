#!/usr/bin/env python
# $Id: Template.py,v 1.139 2006/01/11 22:44:16 tavis_rudd Exp $
"""Provides the core API for Cheetah.

See the docstring in the Template class and the Users' Guide for more information

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@damnsimple.com>
License: This software is released for unlimited distribution under the
         terms of the MIT license.  See the LICENSE file.
Version: $Revision: 1.139 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2006/01/11 22:44:16 $
""" 
__author__ = "Tavis Rudd <tavis@damnsimple.com>"
__revision__ = "$Revision: 1.139 $"[11:-2]

################################################################################
## DEPENDENCIES
import sys                        # used in the error handling code
import re                         # used to define the internal delims regex
import new                        # used to bind methods and create dummy modules
import string
import os.path
import time                       # used in the cache refresh code
from random import randrange
import imp
import traceback
import __builtin__            # sometimes used by dynamically compiled templates
import pprint
import cgi                # Used by .webInput() if the template is a CGI script.
import types 
from types import StringType, ClassType
try:
    from types import StringTypes
except ImportError:
    StringTypes = (types.StringType,types.UnicodeType)
try:
    from threading import Lock
except ImportError:
    class Lock:
        def acquire(self): pass
        def release(self): pass


# Base classes for Template
from Cheetah.Servlet import Servlet                 
# More intra-package imports ...
from Cheetah.Compiler import Compiler, DEFAULT_COMPILER_SETTINGS
from Cheetah import ErrorCatchers              # for placeholder tags
from Cheetah import Filters                    # the output filters
from Cheetah.convertTmplPathToModuleName import convertTmplPathToModuleName
from Cheetah.Utils import VerifyType             # Used in Template.__init__
from Cheetah.Utils.Misc import checkKeywords     # Used in Template.__init__
from Cheetah.Utils.Indenter import Indenter      # Used in Template.__init__ and for
                                                 # placeholders
from Cheetah.NameMapper import NotFound, valueFromSearchList
from Cheetah.CacheRegion import CacheRegion
from Cheetah.Utils.WebInputMixin import _Converter, _lookup, NonNumericInputError
try:
    from ds.sys.Unspecified import Unspecified
except ImportError:
    class _Unspecified:
        def __repr__(self):
            return 'Unspecified'        
        def __str__(self):
            return 'Unspecified'
    Unspecified = _Unspecified()
    
class Error(Exception):  pass
class PreprocessError(Error): pass

################################################################################
## MODULE GLOBALS AND CONSTANTS

_cheetahModuleNames = [] # used by _genUniqueModuleName
_uniqueModuleNameLock = Lock() # _genUniqueModuleName(): prevent collisions in sys.modules
def _genUniqueModuleName(baseModuleName):
    _uniqueModuleNameLock.acquire()
    if baseModuleName not in sys.modules and baseModuleName not in _cheetahModuleNames:
        finalName = baseModuleName
    else:
        finalName = ('cheetah_'+baseModuleName
                     +'_'
                     +''.join(map(lambda x: '%02d' % x, time.localtime(time.time())[:6]))
                     + str(randrange(10000, 99999)))

    _cheetahModuleNames.append(finalName) # prevent collisions
    _uniqueModuleNameLock.release()
    return finalName

# Cache of a cgi.FieldStorage() instance, maintained by .webInput().
# This is only relavent to templates used as CGI scripts.
_formUsedByWebInput = None

        
class Template(Servlet):
    """This provides a) methods used at runtime by templates and b) the
    .compile() classmethod for compiling Cheetah source code into template
    classes.

    This documentation assumes you already know Python and the basics of object
    oriented programming.  If you don't know Python, see the sections of the
    Cheetah Users' Guide for non-programmers.  It also assumes you have read
    about Cheetah's syntax in the Users' Guide.

    The following explains how to use this Cheetah within Python programs or via
    the interpreter. If you statically compile your templates on the command
    line using the 'cheetah' script, this is not relevant to you. Statically
    compiled Cheetah template modules/classes (e.g. myTemplate.py:
    MyTemplateClasss) are just like any other Python module or class. Also note,
    most Python web frameworks (Webware, Aquarium, mod_python, Turbogears,
    CherryPy, Quixote, etc.) provide plugins that Cheetah compilation for you.

    There are several possible usage patterns:          
       1) tmplClass = Template.compile(src)
          tmplInstance1 = tmplClass() # or tmplClass(searchList=[namespace,...])
          tmplInstance2 = tmplClass() # or tmplClass(searchList=[namespace2,...])
          outputStr = str(tmplInstance1) # or outputStr = tmplInstance.aMethodYouDefined()

          Template.compile provides a rich and very flexible API via its
          optional arguments so there are many possible variations of this
          pattern.  One example is:
            tmplClass = Template.compile('hello $name from $caller', baseclass=dict)
            print tmplClass(name='world', caller='me')
          See the Template.compile() docstring for more details.  

       2) tmplInstance = Template(src)
             # or Template(src, searchList=[namespace,...])
          outputStr = str(tmplInstance) # or outputStr = tmplInstance.aMethodYouDefined(...args...)

    Notes on the usage patterns:
    
       1) This is the most flexible, but it is slightly more verbose unless you
          write a wrapper function to hide the plumbing.  Under the hood, all
          other usage patterns are based on this approach.  Templates compiled
          this way can #extend (subclass) any Python baseclass: old-style or
          new-style (based on object or a builtin type).

       2) This was Cheetah's original usage pattern.  It returns an instance,
          but you can still access the generated class via
          tmplInstance.__class__.  If you want to use several different
          'searchLists' with a single template source definition, you're better
          off with Template.compile (1).

          Limitations (use Template.compile (1) instead):
           - Templates compiled this way can only #extend subclasses of the
             new-style 'object' baseclass.  Cheetah.Template is a subclass of
             'object'.  You also can not #extend dict, list, or other builtin
             types.  
           - If your template baseclass' __init__ constructor expects args there
             is currently no way to pass them in.

    If you need to subclass a dynamically compiled Cheetah class, do something like this:
        from Cheetah.Template import Template
        T1 = Template.compile('$meth1 #def meth1: this is meth1 in T1')
        T2 = Template.compile('#implements meth1\nthis is meth1 redefined in T2', baseclass=T1)
        print T1, T1()
        print T2, T2()


    Note about class and instance attribute names:
      Attributes used by Cheetah have a special prefix to avoid confusion with
      the attributes of the templates themselves or those of template
      baseclasses.
      
      Class attributes which are used in class methods look like this:
          klass._CHEETAH_useCompilationCache (_CHEETAH_xxx)

      Instance attributes look like this:
          klass._CHEETAH__globalSetVars (_CHEETAH__xxx with 2 underscores)
    """

    #this is used by .assignRequiredMethodsToClass()
    _CHEETAH_requiredCheetahMethodNames = ('_initCheetahAttributes',
                                           'searchList',
                                           'errorCatcher',
                                           'refreshCache',
                                           'getVar',
                                           'varExists',
                                           'getFileContents',
                                           'runAsMainProgram',
                                           
                                           '_handleCheetahInclude',
                                           )

    # the following are used by .compile()
    _CHEETAH_keepGeneratedPythonModulesForTracebacks = False
    _CHEETAH_cacheDirForGeneratedPythonModules = None # change to a dirname
    _CHEETAH_compileLock = Lock() # used to prevent race conditions
    _CHEETAH_compileCache = dict()
    #
    _CHEETAH_defaultMainMethodName = None
    _CHEETAH_compilerSettings = None
    _CHEETAH_compilerClass = Compiler
    _CHEETAH_cacheCompilationResults = True
    _CHEETAH_useCompilationCache = True
    _CHEETAH_preprocessors = None
    _CHEETAH_keepRefToGeneratedCode = True
    _CHEETAH_defaultBaseclassForTemplates = None
    _CHEETAH_defaultClassNameForTemplates = None
    # defaults to DEFAULT_COMPILER_SETTINGS['mainMethodName']:
    _CHEETAH_defaultMainMethodNameForTemplates = None 
    _CHEETAH_defaultModuleNameForTemplates = 'DynamicallyCompiledCheetahTemplate'
    _CHEETAH_defaultModuleGlobalsForTemplates = None
    
    # The following 3 are used by instance methods.
    _CHEETAH_generatedModuleCode = None
    _CHEETAH_generatedClassCode = None            
    NonNumericInputError = NonNumericInputError

    def _getCompilerClass(klass, source=None, file=None):
        return klass._CHEETAH_compilerClass
    _getCompilerClass = classmethod(_getCompilerClass)

    def _getCompilerSettings(klass, source=None, file=None):
        return klass._CHEETAH_compilerSettings
    _getCompilerSettings = classmethod(_getCompilerSettings)
    
    def compile(klass, source=None, file=None,
                returnAClass=True,
                
                compilerSettings=Unspecified,
                compilerClass=Unspecified,
                moduleName=None,
                className=Unspecified,
                mainMethodName=Unspecified,
                baseclass=Unspecified,
                moduleGlobals=Unspecified,
                cacheCompilationResults=Unspecified,
                useCache=Unspecified,
                preprocessors=Unspecified,                
                keepRefToGeneratedCode=Unspecified,
                ):
        """
        The core API for compiling Cheetah source code into template classes.

        This class method compiles Cheetah source code and returns a python
        class.  You then create template instances using that class.  All
        Cheetah's other compilation API's use this method under the hood.

        If you want to get the generated python source code instead, pass the
        argument returnAClass=False.

        Args:
          You must provide either a 'source' or 'file' arg, but not both:
            - source (string or None)
            - file (string path, file-like object, or None)

          The rest of the arguments are strictly optional. All but the first
          have defaults in attributes of the Template class which can be
          overridden in subclasses.  Working with most of these is an advanced
          topic.
          
            - returnAClass=True            
              If false, return the generated module code rather than a class.

            - compilerSettings (a dict)
              Default: Template._CHEETAH_compilerSettings=None
            
              a dictionary of settings to override those defined in
              DEFAULT_COMPILER_SETTINGS. 
                  
            - compilerClass (a class)
              Default: Template._CHEETAH_compilerClass=Cheetah.Compiler.Compiler
            
              a subclass of Cheetah.Compiler.Compiler. Mucking with this is a
              very advanced topic.
                  
            - moduleName (a string)
              Default:
                  Template._CHEETAH_defaultModuleNameForTemplates
                  ='DynamicallyCompiledCheetahTemplate'
            
              What to name the generated Python module.  If the provided value is
              None and a file arg was given, the moduleName is created from the
              file path.  In all cases if the moduleName provided is already in
              sys.modules it is passed through a filter that generates a unique
              variant of the name.


            - className (a string)
              Default: Template._CHEETAH_defaultClassNameForTemplates=None
              
              What to name the generated Python class.  If the provided value is
              None, the moduleName is use as the class name.

            - mainMethodName (a string)
              Default:
                  Template._CHEETAH_defaultMainMethodNameForTemplates
                  =None (and thus DEFAULT_COMPILER_SETTINGS['mainMethodName']) 
            
              What to name the main output generating method in the compiled
              template class.  

            - baseclass (a string or a class)
              Default: Template._CHEETAH_defaultBaseclassForTemplates=None

              Specifies the baseclass for the template without manually
              including an #extends directive in the source. The #extends
              directive trumps this arg.

              If the provided value is a string you must make sure that a class
              reference by that name is available to your template, either by
              using an #import directive or by providing it in the arg
              'moduleGlobals'.  

              If the provided value is a class, Cheetah will handle all the
              details for you.

            - moduleGlobals (a dict)
              A dict of vars that will be added to the global namespace of the
              module the generated code is executed in, prior to the execution
              of that code.  This should be Python values, not code strings!
              
              Default:
                  Template._CHEETAH_defaultModuleGlobalsForTemplates
                  =None

            - cacheCompilationResults (True/False)
              Default: Template._CHEETAH_cacheCompilationResults=True

              Tells Cheetah to cache the generated code and classes so that they
              can be reused if Template.compile() is called multiple times with
              the same source and options.
              
              
            - useCache (True/False)
              Default: Template._CHEETAH_useCompilationCache=True

              Should the compilation cache be used.              

            - preprocessors
              Default: Template._CHEETAH_preprocessors=None

              (A VERY ADVANCED TOPIC)
               
              These are used to transform the source code prior to compilation.
              The major expected use cases are:
                  
                a) 'compile-time caching' aka 'partial template binding',
                   wherein an intermediate Cheetah template is used to output
                   the source for the final Cheetah template. The intermediate
                   template is a mix of a modified Cheetah syntax (the
                   'preprocess syntax') and standard Cheetah syntax.  This
                   approach allows one to completely soft-code all the elements
                   in the template which are subject to change yet have it
                   compile to extremely efficient Python code with everything
                   but the elements that must be variable at runtime (per
                   browser request, etc.) compiled as static strings.  Examples
                   of this usage pattern will be added to the Cheetah Users'
                   Guide.
                
                b) adding #import and #extends directives dynamically based on
                   the source
                
              If preprocessors are provided, Cheetah pipes the source code
              through each one in the order provided.  Each preprocessor should
              accept the args (source, file) and should return a tuple (source,
              file).

              The argument value should be a list, but a single non-list value
              is acceptable and will automatically be converted into a list.
              Each item in the list will be passed through
              Template._normalizePreprocessor().  The items should either match
              one of the following forms:
                - an object with a .preprocess(source, file) method
                - a callable with the signature f(source, file)
                
                or one of the forms below. This second set of forms is used to
                create a preprocessor which assumes you are doing 'compile-time
                caching' described above in use case (a).  The 'preprocess
                syntax' used is the just standard one with a prefix appended to
                cheetahVarStartToken, directiveStartToken, commentStartToken,
                and multiLineCommentStartToken in the preprocess placeholders
                and directives in the source:
                    
                    e.g. '1:' for code like this
                     $1:aPreprocessVar $aRuntimeVar
                     #1:if xxx then yyy else zzz
                
                - a single string denoting the 'prefix' for the preprocess syntax
                - a dict with the following keys or an object with the
                  following attributes (all are optional, but nothing will
                  happen if you don't provide at least one):
                   - prefix: same as the single string described above
                   - searchList: the searchList used for preprocess $placeholders
                   - compilerSettings: used in the compilation of the intermediate
                     template                
                   - compiler: used in the compilation of the preprocess template                
                   - outputTransformer: a simple hook for passing in a callable
                     which can do further transformations of the preprocessor
                     output, or do something else like debug logging. The
                     default is str().
            
        """

        ##################################################           
        ## normalize args        
        try:
            vt = VerifyType.VerifyType
            vtc = VerifyType.VerifyTypeClass
            N = types.NoneType; S = types.StringType; U = types.UnicodeType
            D = types.DictType; F = types.FileType
            C = types.ClassType;  M = types.ModuleType
            B = types.BooleanType; I = types.IntType

            vt(source, 'source', [N,S,U], 'string or None')
            vt(file, 'file',[N,S,U,F], 'string, file-like object, or None')
            def valOrDefault(val, default):                
                if val is not Unspecified: return val
                else: return default

            baseclass = valOrDefault(baseclass, klass._CHEETAH_defaultBaseclassForTemplates)
            vt(baseclass, 'baseclass', [N,S,C,type], 'string, class or None')

            cacheCompilationResults = valOrDefault(
                cacheCompilationResults, klass._CHEETAH_cacheCompilationResults)
            vt(cacheCompilationResults, 'cacheCompilationResults', [I,B], 'boolean')

            useCache = valOrDefault(useCache, klass._CHEETAH_useCompilationCache)
            vt(cacheCompilationResults, 'cacheCompilationResults', [I,B], 'boolean')

            compilerSettings = valOrDefault(
                compilerSettings, klass._getCompilerSettings(source, file) or {})
            vt(compilerSettings, 'compilerSettings', [D], 'dictionary')

            compilerClass = valOrDefault(compilerClass, klass._getCompilerClass(source, file))

            preprocessors = valOrDefault(preprocessors, klass._CHEETAH_preprocessors)

            keepRefToGeneratedCode = valOrDefault(
                keepRefToGeneratedCode, klass._CHEETAH_keepRefToGeneratedCode)
            vt(cacheCompilationResults, 'cacheCompilationResults', [I,B], 'boolean')

            vt(moduleName, 'moduleName', [N,S], 'string or None')
            __orig_file__ = None
            if not moduleName:
                if file and type(file) in StringTypes:
                    moduleName = convertTmplPathToModuleName(file)
                    __orig_file__ = file
                else:
                    moduleName = klass._CHEETAH_defaultModuleNameForTemplates
            uniqueModuleName = _genUniqueModuleName(moduleName)
            
            className = valOrDefault(
                className, klass._CHEETAH_defaultClassNameForTemplates)
            vt(className, 'className', [N,S], 'string or None')
            className = className or moduleName

            mainMethodName = valOrDefault(
                mainMethodName, klass._CHEETAH_defaultMainMethodNameForTemplates)
            vt(mainMethodName, 'mainMethodName', [N,S], 'string or None')

            moduleGlobals = valOrDefault(
                moduleGlobals, klass._CHEETAH_defaultModuleGlobalsForTemplates)
        except TypeError, reason:
            raise TypeError(reason)

        ##################################################           
        ## handle any preprocessors
        if preprocessors:
            origSrc = source
            source, file = klass._preprocessSource(source, file, preprocessors)

        ##################################################                       
        ## compilation, using cache if requested/possible
        baseclassValue = None
        baseclassName = None
        if baseclass:
            if type(baseclass) in StringTypes:
                baseclassName = baseclass
            elif type(baseclass) in (ClassType, type):
                baseclassName = 'CHEETAH_dynamicallyAssignedBaseClass'
                baseclassValue = baseclass


        cacheHash = None
        cachedResults = None
        if source and not file:
            compilerSettingsHash = None
            if compilerSettings:
                items = compilerSettings.items()
                items.sort()
                compilerSettingsHash = hash(tuple(items))
            cacheHash = ''.join([str(v) for v in
                                 [hash(source),
                                  str(moduleName),
                                  str(mainMethodName),
                                  hash(compilerClass),
                                  hash(baseclass),
                                  compilerSettingsHash]])
            
        if useCache and cacheHash and cacheHash in klass._CHEETAH_compileCache:
            cachedResults = klass._CHEETAH_compileCache[cacheHash]
            generatedModuleCode = cachedResults.code
        else:
            compiler = compilerClass(source, file,
                                     moduleName=moduleName,
                                     mainClassName=className,
                                     baseclassName=baseclassName,
                                     mainMethodName=mainMethodName,
                                     settings=(compilerSettings or {}))
            compiler.compile()
            generatedModuleCode = compiler.getModuleCode()
        
        if returnAClass:
            if cachedResults:
                return cachedResults.klass

            __file__ = uniqueModuleName+'.py' # relative file path with no dir part

            if klass._CHEETAH_keepGeneratedPythonModulesForTracebacks:
                if not os.path.exists(klass._CHEETAH_cacheDirForGeneratedPythonModules):
                    raise Exception('%s does not exist'%
                                    klass._CHEETAH_cacheDirForGeneratedPythonModules)

                __file__ = os.path.join(klass._CHEETAH_cacheDirForGeneratedPythonModules,
                                        __file__)
                klass._compileLock.acquire()
                try:
                    # @@TR: might want to assert that it doesn't already exist
                    try:
                        open(__file__, 'w').write(generatedModuleCode)
                        # @@TR: should probably restrict the perms, etc.
                    except OSError:
                        # @@ TR: should this optionally raise?
                        traceback.print_exc(file=sys.stderr)
                finally:
                    klass._compileLock.release()
            try:
                co = compile(generatedModuleCode, __file__, 'exec')
            except:
                print generatedModuleCode
                raise
            mod = new.module(uniqueModuleName)
            mod.__file__ = __file__
            if __orig_file__ and os.path.exists(__orig_file__):
                # this is used in the WebKit filemonitoring code
                mod.__orig_file__ = __orig_file__

            if moduleGlobals:
                for k, v in moduleGlobals.items():
                    setattr(mod, k, v)

            if baseclass and baseclassValue:
                setattr(mod, baseclassName, baseclassValue)
            exec co in mod.__dict__

            sys.modules[uniqueModuleName] = mod
            templateClass = getattr(mod, className)

            if keepRefToGeneratedCode:
                templateClass._CHEETAH_generatedModuleCode = generatedModuleCode
                templateClass._CHEETAH_generatedClassCode = str(
                    compiler._finishedClassIndex[moduleName])

            if cacheCompilationResults and cacheHash:
                class CacheResults: pass;
                cacheResults = CacheResults()
                cacheResults.code = generatedModuleCode
                cacheResults.klass = templateClass
                klass._CHEETAH_compileCache[cacheHash] = cacheResults
            return templateClass
        else:
            return generatedModuleCode
    compile = classmethod(compile)

    def subclass(klass, *args, **kws):
        """Takes the same args as the .compile() classmethod and returns a
        template that is a subclass of the template this method is called from.

          T1 = Template.compile(' foo - $meth1 - bar\n#def meth1: this is T1.meth1')
          T2 = T1.subclass('#implements meth1\n this is T2.meth1')
        """
        kws['baseclass'] = klass
        if isinstance(klass, Template):
            templateAPIClass = klass
        else:
            templateAPIClass = Template
        return templateAPIClass.compile(*args, **kws)
    subclass = classmethod(subclass)

    def _preprocessSource(klass, source, file, preprocessors):
        """Iterates through the .compile() classmethod's preprocessors argument
        and pipes the source code through each each preprocessor.

        It returns the tuple (source, file) which is then used by
        Template.compile to finish the compilation.
        """
        if not source: # @@TR: this needs improving
            if isinstance(file, (str, unicode)): # it's a filename.
                f = open(file)
                source = f.read()
                f.close()
            elif hasattr(file, 'read'):
                source = file.read()
            file = None        
        if not isinstance(preprocessors, (list, tuple)):
            preprocessors = [preprocessors]
        for preprocessor in preprocessors:
            preprocessor = klass._normalizePreprocessor(preprocessor)
            source = preprocessor.preprocess(source)
        return source, file
    _preprocessSource = classmethod(_preprocessSource)

    def _normalizePreprocessor(klass, input):
        """Used to convert the items in the .compile() classmethod's
        preprocessors argument into real source preprocessors.  This permits the
        use of several shortcut forms for defining preprocessors.
        """
        if hasattr(input, 'preprocess'):
            return input
        elif callable(input):
            class Preprocessor:
                def preprocess(self, src):
                    return input(src)
            return Preprocessor()

        ##
        class Options(object): pass
        options = Options()
        options.searchList = []
        options.keepRefToGeneratedCode = True
        
        def normalizeSearchList(searchList):
            if not isinstance(searchList, (list, tuple)):
                searchList = [searchList]
            return searchList            
        
        if isinstance(input, str):
            options.prefix = input            
        elif isinstance(input, dict):
            options.prefix = input.get('prefix')
            options.searchList = normalizeSearchList(
                input.get('searchList',
                          input.get('namespaces', [])))            
            for k, v in input.items():
                setattr(options, k, v)
        else: #it's an options object
            options = input

        if not hasattr(options, 'outputTransformer'):            
            options.outputTransformer = str

        if not hasattr(options, 'compiler'):
            def createPreprocessCompiler(prefix, compilerSettings=None):
                class PreprocessorCompiler(klass):
                    _compilerSettings = dict(
                        cheetahVarStartToken='$'+prefix,
                        directiveStartToken='#'+prefix,
                        commentStartToken='##'+prefix,
                        multiLineCommentStartToken='#*'+prefix,
                        )
                    if compilerSettings:
                        _compilerSettings.update(compilerSettings)
                return PreprocessorCompiler

            compilerSettings = getattr(options, 'compilerSettings', None)
            if not compilerSettings and not options.prefix:
                raise TypeError(
                    'Preprocessor requires either a "prefix" or a "compilerSettings" arg.'
                    ' Neither was provided.')
            options.compiler = createPreprocessCompiler(
                prefix=options.prefix,
                compilerSettings=compilerSettings,
                )

        class Preprocessor:
            def preprocess(self, source):
                moduleGlobals = getattr(options, 'moduleGlobals', None)
                templClass = options.compiler.compile(
                    source,
                    keepRefToGeneratedCode=options.keepRefToGeneratedCode,
                    moduleGlobals=moduleGlobals,
                    )
                instance = templClass(searchList=options.searchList)
                source = options.outputTransformer(instance)
                return source
        return Preprocessor()
    _normalizePreprocessor = classmethod(_normalizePreprocessor)        

    def _assignRequiredMethodsToClass(klass, concreteTemplateClass):
        """If concreteTemplateClass is not a subclass of Cheetah.Template, add
        the required cheetah methods to it.

        This is called on each new template class after it has been compiled.
        If concreteTemplateClass is not a subclass of Cheetah.Template but
        already has method with the same name as one of the required cheetah
        methods, this will skip that method.
        """
        for methodname in klass._CHEETAH_requiredCheetahMethodNames:
            if not hasattr(concreteTemplateClass, methodname):
                method = getattr(Template, methodname)
                newMethod = new.instancemethod(method.im_func, None, concreteTemplateClass)
                #print methodname, method
                setattr(concreteTemplateClass, methodname, newMethod)

        if (not hasattr(concreteTemplateClass, '__str__')
            or concreteTemplateClass.__str__ is object.__str__):
            
            mainMethNameAttr = '_mainCheetahMethod_for_'+concreteTemplateClass.__name__
            mainMethName = getattr(concreteTemplateClass,mainMethNameAttr, None)
            if mainMethName:
                def __str__(self): return getattr(self, mainMethName)()
            elif hasattr(concreteTemplateClass, 'respond'):
                def __str__(self): return self.respond()
            else:
                def __str__(self):
                    if hasattr(self, mainMethNameAttr):
                        return getattr(self,mainMethNameAttr)()
                    elif hasattr(self, 'respond'):
                        return self.respond()
                    else:
                        return super(self.__class__, self).__str__()
                    
            __str__ = new.instancemethod(__str__, None, concreteTemplateClass)
            setattr(concreteTemplateClass, '__str__', __str__)            
                
    _assignRequiredMethodsToClass = classmethod(_assignRequiredMethodsToClass)

    ## end classmethods ##

    def __init__(self, source=None, searchList=Unspecified, namespaces=Unspecified,
                 file=None,
                 filter='EncodeUnicode', # which filter from Cheetah.Filters
                 filtersLib=Filters,
                 errorCatcher=None,
                 
                 compilerSettings=Unspecified, # control the behaviour of the compiler
                 _globalSetVars=Unspecified, # used internally for #include'd templates
                 _preBuiltSearchList=Unspecified # used internally for #include'd templates
                 ):        
        """Reads in the template definition, sets up the namespace searchList,
        processes settings, then compiles.

        Compiler configuration settings should be passed in as a dictionary via
        the 'compilerSettings' keyword.

        This method can also be called without arguments in cases where it is
        called as a baseclass from a pre-compiled Template servlet.
        """
        
        ##################################################           
        ## Verify argument keywords and types

        S = types.StringType; U = types.UnicodeType
        L = types.ListType;   T = types.TupleType
        D = types.DictType;   F = types.FileType
        C = types.ClassType;  M = types.ModuleType
        N = types.NoneType
        vt = VerifyType.VerifyType
        vtc = VerifyType.VerifyTypeClass
        try:
            vt(source, 'source', [N,S,U], 'string or None')
            vt(file, 'file', [N,S,U,F], 'string, file open for reading, or None')
            vtc(filter, 'filter', [S,C], 'string or class', 
                Filters.Filter,
                '(if class, must be subclass of Cheetah.Filters.Filter)')
            vt(filtersLib, 'filtersLib', [S,M], 'string or module',
                '(if module, must contain subclasses of Cheetah.Filters.Filter)')
            vtc(errorCatcher, 'errorCatcher', [N,S,C], 'string, class or None',
               ErrorCatchers.ErrorCatcher,
               '(if class, must be subclass of Cheetah.ErrorCatchers.ErrorCatcher)')
            if compilerSettings is not Unspecified:
                vt(compilerSettings, 'compilerSettings', [D], 'dictionary')

            if namespaces is not Unspecified: 
                assert not searchList
                searchList = namespaces           
            if not isinstance(searchList, (list, tuple)):
                searchList = [searchList]

        except TypeError, reason:
            # Re-raise the exception here so that the traceback will end in
            # this function rather than in some utility function.
            raise TypeError(reason)
        
        if source is not None and file is not None:
            raise TypeError("you must supply either a source string or the" + 
                            " 'file' keyword argument, but not both")
                    
        ##################################################           
        ## Do superclass initialization.
        Servlet.__init__(self)

        ##################################################           
        ## Setup instance state attributes used during the life of template
        ## post-compile

        self._initCheetahAttributes(
            searchList=searchList, filter=filter, filtersLib=filtersLib,
            errorCatcher=errorCatcher,
            _globalSetVars=_globalSetVars,
            _preBuiltSearchList=_preBuiltSearchList)
        
        ##################################################
        ## Now, compile if we're meant to
        if (source is not None) or (file is not None):
            self._compile(source, file, compilerSettings=compilerSettings)

    def generatedModuleCode(self):
        """Return the module code the compiler generated, or None if no
        compilation took place.
        """
        
        return self._CHEETAH_generatedModuleCode
    
    def generatedClassCode(self):        
        """Return the class code the compiler generated, or None if no
        compilation took place.
        """

        return self._CHEETAH_generatedClassCode
    
    def searchList(self):
        """Return a reference to the searchlist
        """
        return self._CHEETAH__searchList

    def errorCatcher(self):
        """Return a reference to the current errorCatcher
        """
        return self._CHEETAH__errorCatcher

    def refreshCache(self, cacheRegionKey=None, cacheKey=None):        
        """Refresh a cache item.
        """
        
        if not cacheRegionKey:
            # clear all template's cache regions
            self._CHEETAH__cacheRegions.clear()
        else:
            region = self._CHEETAH__cacheRegions.get(cacheRegionKey, CacheRegion())
            if not cacheKey:
                # clear the desired region and all its cache
                region.clear()
            else:
                # clear one specific cache of a specific region
                cache = region.getCache(cacheKey)
                if cache:
                    cache.clear()

    def shutdown(self):
        """Break reference cycles before discarding a servlet.
        """
        try:
            Servlet.shutdown(self)
        except:
            pass
        self._CHEETAH__searchList = None
        self.__dict__ = {}
            
    ## utility functions ##   

    def getVar(self, varName, default=Unspecified, autoCall=True):        
        """Get a variable from the searchList.  If the variable can't be found
        in the searchList, it returns the default value if one was given, or
        raises NameMapper.NotFound.
        """
        
        try:
            return valueFromSearchList(self.searchList(), varName.replace('$',''), autoCall)
        except NotFound:
            if default is not Unspecified:
                return default
            else:
                raise
    
    def varExists(self, varName, autoCall=True):
        """Test if a variable name exists in the searchList.
        """
        try:
            valueFromSearchList(self.searchList(), varName.replace('$',''), autoCall)
            return True
        except NotFound:
            return False


    hasVar = varExists
    

    def getFileContents(self, path):
        """A hook for getting the contents of a file.  The default
        implementation just uses the Python open() function to load local files.
        This method could be reimplemented to allow reading of remote files via
        various protocols, as PHP allows with its 'URL fopen wrapper'
        """
        
        fp = open(path,'r')
        output = fp.read()
        fp.close()
        return output
    
    def runAsMainProgram(self):        
        """Allows the Template to function as a standalone command-line program
        for static page generation.

        Type 'python yourtemplate.py --help to see what it's capabable of.
        """

        from TemplateCmdLineIface import CmdLineIface
        CmdLineIface(templateObj=self).run()
        
    ##################################################
    ## internal methods -- not to be called by end-users

    def _initCheetahAttributes(self,
                               searchList=Unspecified,
                               filter='EncodeUnicode', # which filter from Cheetah.Filters
                               filtersLib=Filters,
                               errorCatcher=None,
                               _globalSetVars=Unspecified,
                               _preBuiltSearchList=Unspecified):
        """Sets up the instance attributes that cheetah templates use at
        run-time.

        This is automatically called by the __init__ method of compiled templates.
        """
        if getattr(self, '_CHEETAH__instanceInitialized', False):
            return
        
        self._CHEETAH__globalSetVars = {}
        if _globalSetVars is not Unspecified:
            # this is intended to be used internally by Nested Templates in #include's
            self._CHEETAH__globalSetVars = _globalSetVars
            
        if _preBuiltSearchList is not Unspecified:
            # happens with nested Template obj creation from #include's
            self._CHEETAH__searchList = list(_preBuiltSearchList)
            self._CHEETAH__searchList.append(self)
        else:
            # create our own searchList
            self._CHEETAH__searchList = [self._CHEETAH__globalSetVars]
            if searchList is not Unspecified:
                self._CHEETAH__searchList.extend(list(searchList))
            self._CHEETAH__searchList.append( self )
        self._CHEETAH__cheetahIncludes = {}
        self._CHEETAH__cacheRegions = {}
        self._CHEETAH__indenter = Indenter()
        self._CHEETAH__filtersLib = filtersLib
        self._CHEETAH__filters = {}
        if type(filter) in StringTypes:
            filterName = filter
            klass = getattr(self._CHEETAH__filtersLib, filterName)
        else:
            klass = filter
            filterName = klass.__name__            
        self._CHEETAH__currentFilter = self._CHEETAH__filters[filterName] = klass(self).filter
        self._CHEETAH__initialFilter = self._CHEETAH__currentFilter
        self._CHEETAH__errorCatchers = {}
        if errorCatcher:
            if type(errorCatcher) in StringTypes:
                errorCatcherClass = getattr(ErrorCatchers, errorCatcher)
            elif type(errorCatcher) == ClassType:
                errorCatcherClass = errorCatcher

            self._CHEETAH__errorCatcher = ec = errorCatcherClass(self)
            self._CHEETAH__errorCatchers[errorCatcher.__class__.__name__] = ec
                                 
        else:
            self._CHEETAH__errorCatcher = None
        self._CHEETAH__initErrorCatcher = self._CHEETAH__errorCatcher        

        if not hasattr(self, 'transaction'):
            self.transaction = None
        self._CHEETAH__instanceInitialized = True
        self._CHEETAH__isBuffering = False
            
    def _compile(self, source=None, file=None, compilerSettings=Unspecified,
                 moduleName=None, mainMethodName=None):
        """Compile the template. This method is automatically called by
        Template.__init__ it is provided with 'file' or 'source' args.

        USERS SHOULD *NEVER* CALL THIS METHOD THEMSELVES.  Use Template.compile
        instead.
        """
        if compilerSettings is Unspecified:
            compilerSettings = self._getCompilerSettings(source, file) or {}        
        mainMethodName = mainMethodName or self._CHEETAH_defaultMainMethodName
        self._fileMtime = None
        self._fileDirName = None
        self._fileBaseName = None
        if file and type(file) in StringTypes:
            file = self.serverSidePath(file)
            self._fileMtime = os.path.getmtime(file)
            self._fileDirName, self._fileBaseName = os.path.split(file)
        self._filePath = file
        templateClass = self.compile(source, file,
                                      moduleName=moduleName,
                                      mainMethodName=mainMethodName,
                                      compilerSettings=compilerSettings,
                                      keepRefToGeneratedCode=True)
        self.__class__ = templateClass
        # must initialize it so instance attributes are accessible
        templateClass.__init__(self,
                               #_globalSetVars=self._CHEETAH__globalSetVars,
                               #_preBuiltSearchList=self._CHEETAH__searchList
                               )                               
        if not hasattr(self, 'transaction'):
            self.transaction = None

    def _handleCheetahInclude(self, srcArg, trans=None, includeFrom='file', raw=False):        
        """Called at runtime to handle #include directives.
        """
        _includeID = srcArg            
        if not self._CHEETAH__cheetahIncludes.has_key(_includeID):
            if not raw:
                if includeFrom == 'file':
                    source = None
                    if type(srcArg) in StringTypes:
                        file = path = self.serverSidePath(srcArg)
                    else:
                        file = srcArg ## a file-like object
                else:
                    source = srcArg
                    file = None
                # @@TR: might want to provide some syntax for specifying the
                # Template class to be used for compilation so compilerSettings
                # can be changed.
                compiler = self._getTemplateClassForIncludeCompilation(source, file)
                nestedTemplateClass = compiler.compile(source=source,file=file)
                nestedTemplate = nestedTemplateClass(_preBuiltSearchList=self.searchList(),
                                                     _globalSetVars=self._CHEETAH__globalSetVars)
                self._CHEETAH__cheetahIncludes[_includeID] = nestedTemplate
            else:
                if includeFrom == 'file':
                    path = self.serverSidePath(srcArg)
                    self._CHEETAH__cheetahIncludes[_includeID] = self.getFileContents(path)
                else:
                    self._CHEETAH__cheetahIncludes[_includeID] = srcArg
        ##
        if not raw:
            self._CHEETAH__cheetahIncludes[_includeID].respond(trans)
        else:
            trans.response().write(self._CHEETAH__cheetahIncludes[_includeID])

    def _getTemplateClassForIncludeCompilation(self, source, file):
        """Returns the subclass of Template which should be used to compile
        #include directives.

        This abstraction allows different compiler settings to be used in the
        included template than were used in the parent.
        """
        return self.__class__

    ## functions for using templates as CGI scripts
    def webInput(self, names, namesMulti=(), default='', src='f',
        defaultInt=0, defaultFloat=0.00, badInt=0, badFloat=0.00, debug=False):
        """Method for importing web transaction variables in bulk.

        This works for GET/POST fields both in Webware servlets and in CGI
        scripts, and for cookies and session variables in Webware servlets.  If
        you try to read a cookie or session variable in a CGI script, you'll get
        a RuntimeError.  'In a CGI script' here means 'not running as a Webware
        servlet'.  If the CGI environment is not properly set up, Cheetah will
        act like there's no input.

        The public method provided is:

          def webInput(self, names, namesMulti=(), default='', src='f',
            defaultInt=0, defaultFloat=0.00, badInt=0, badFloat=0.00, debug=False):

        This method places the specified GET/POST fields, cookies or session
        variables into a dictionary, which is both returned and put at the
        beginning of the searchList.  It handles:
            
            * single vs multiple values
            * conversion to integer or float for specified names
            * default values/exceptions for missing or bad values
            * printing a snapshot of all values retrieved for debugging        

        All the 'default*' and 'bad*' arguments have 'use or raise' behavior,
        meaning that if they're a subclass of Exception, they're raised.  If
        they're anything else, that value is substituted for the missing/bad
        value.


        The simplest usage is:

            #silent $webInput(['choice'])
            $choice

            dic = self.webInput(['choice'])
            write(dic['choice'])

        Both these examples retrieves the GET/POST field 'choice' and print it.
        If you leave off the'#silent', all the values would be printed too.  But
        a better way to preview the values is

            #silent $webInput(['name'], $debug=1)

        because this pretty-prints all the values inside HTML <PRE> tags.

        ** KLUDGE: 'debug' is supposed to insert into the template output, but it
        wasn't working so I changed it to a'print' statement.  So the debugging
        output will appear wherever standard output is pointed, whether at the
        terminal, in a Webware log file, or whatever. ***

        Since we didn't specify any coversions, the value is a string.  It's a
        'single' value because we specified it in 'names' rather than
        'namesMulti'. Single values work like this:
        
            * If one value is found, take it.
            * If several values are found, choose one arbitrarily and ignore the rest.
            * If no values are found, use or raise the appropriate 'default*' value.

        Multi values work like this:
            * If one value is found, put it in a list.
            * If several values are found, leave them in a list.
            * If no values are found, use the empty list ([]).  The 'default*' 
              arguments are *not* consulted in this case.

        Example: assume 'days' came from a set of checkboxes or a multiple combo
        box on a form, and the user  chose'Monday', 'Tuesday' and 'Thursday'.

            #silent $webInput([], ['days'])
            The days you chose are: #slurp
            #for $day in $days
            $day #slurp
            #end for

            dic = self.webInput([], ['days'])
            write('The days you chose are: ')
            for day in dic['days']:
                write(day + ' ')

        Both these examples print:  'The days you chose are: Monday Tuesday Thursday'.

        By default, missing strings are replaced by '' and missing/bad numbers
        by zero.  (A'bad number' means the converter raised an exception for
        it, usually because of non-numeric characters in the value.)  This
        mimics Perl/PHP behavior, and simplifies coding for many applications
        where missing/bad values *should* be blank/zero.  In those relatively
        few cases where you must distinguish between empty-string/zero on the
        one hand and missing/bad on the other, change the appropriate
        'default*' and 'bad*' arguments to something like: 

            * None
            * another constant value
            * $NonNumericInputError/self.NonNumericInputError
            * $ValueError/ValueError
            
        (NonNumericInputError is defined in this class and is useful for
        distinguishing between bad input vs a TypeError/ValueError thrown for
        some other rason.)

        Here's an example using multiple values to schedule newspaper
        deliveries.  'checkboxes' comes from a form with checkboxes for all the
        days of the week.  The days the user previously chose are preselected.
        The user checks/unchecks boxes as desired and presses Submit.  The value
        of 'checkboxes' is a list of checkboxes that were checked when Submit
        was pressed.  Our task now is to turn on the days the user checked, turn
        off the days he unchecked, and leave on or off the days he didn't
        change.

            dic = self.webInput([], ['dayCheckboxes'])
            wantedDays = dic['dayCheckboxes'] # The days the user checked.
            for day, on in self.getAllValues():
                if   not on and wantedDays.has_key(day):
                    self.TurnOn(day)
                    # ... Set a flag or insert a database record ...
                elif on and not wantedDays.has_key(day):
                    self.TurnOff(day)
                    # ... Unset a flag or delete a database record ...

        'source' allows you to look up the variables from a number of different
        sources:
            'f'   fields (CGI GET/POST parameters)
            'c'   cookies
            's'   session variables
            'v'   'values', meaning fields or cookies

        In many forms, you're dealing only with strings, which is why the
        'default' argument is third and the numeric arguments are banished to
        the end.  But sometimes you want automatic number conversion, so that
        you can do numeric comparisions in your templates without having to
        write a bunch of conversion/exception handling code.  Example:

            #silent $webInput(['name', 'height:int'])
            $name is $height cm tall.
            #if $height >= 300
            Wow, you're tall!
            #else
            Pshaw, you're short.
            #end if

            dic = self.webInput(['name', 'height:int'])
            name = dic[name]
            height = dic[height]
            write('%s is %s cm tall.' % (name, height))
            if height > 300:
                write('Wow, you're tall!')
            else:
                write('Pshaw, you're short.')

        To convert a value to a number, suffix ':int' or ':float' to the name.
        The method will search first for a 'height:int' variable and then for a
        'height' variable.  (It will be called 'height' in the final
        dictionary.)  If a numeric conversion fails, use or raise 'badInt' or
        'badFloat'.  Missing values work the same way as for strings, except the
        default is 'defaultInt' or 'defaultFloat' instead of 'default'.

        If a name represents an uploaded file, the entire file will be read into
        memory.  For more sophistocated file-upload handling, leave that name
        out of the list and do your own handling, or wait for
        Cheetah.Utils.UploadFileMixin.

        This only in a subclass that also inherits from Webware's Servlet or
        HTTPServlet.  Otherwise you'll get an AttributeError on 'self.request'.

        EXCEPTIONS: ValueError if 'source' is not one of the stated characters.
        TypeError if a conversion suffix is not ':int' or ':float'.

        FUTURE EXPANSION: a future version of this method may allow source
        cascading; e.g., 'vs' would look first in 'values' and then in session
        variables.

        Meta-Data
        ================================================================================
        Author: Mike Orr <iron@mso.oz.net>
        License: This software is released for unlimited distribution under the
                 terms of the MIT license.  See the LICENSE file.
        Version: $Revision: 1.139 $
        Start Date: 2002/03/17
        Last Revision Date: $Date: 2006/01/11 22:44:16 $
        """ 
        src = src.lower()
        isCgi = not self.isControlledByWebKit
        if   isCgi and src in ('f', 'v'):
            global _formUsedByWebInput
            if _formUsedByWebInput is None:
                _formUsedByWebInput = cgi.FieldStorage()
            source, func = 'field',   _formUsedByWebInput.getvalue
        elif isCgi and src == 'c':
            raise RuntimeError("can't get cookies from a CGI script")
        elif isCgi and src == 's':
            raise RuntimeError("can't get session variables from a CGI script")
        elif isCgi and src == 'v':
            source, func = 'value',   self.request().value
        elif isCgi and src == 's':
            source, func = 'session', self.request().session().value
        elif src == 'f':
            source, func = 'field',   self.request().field
        elif src == 'c':
            source, func = 'cookie',  self.request().cookie
        elif src == 'v':
            source, func = 'value',   self.request().value
        elif src == 's':
            source, func = 'session', self.request().session().value
        else:
            raise TypeError("arg 'src' invalid")
        sources = source + 's'
        converters = {
            ''     : _Converter('string', None, default,      default ),
            'int'  : _Converter('int',     int, defaultInt,   badInt  ),
            'float': _Converter('float', float, defaultFloat, badFloat),  }
        #pprint.pprint(locals());  return {}
        dic = {} # Destination.
        for name in names:
            k, v = _lookup(name, func, False, converters)
            dic[k] = v
        for name in namesMulti:
            k, v = _lookup(name, func, True, converters)
            dic[k] = v
        # At this point, 'dic' contains all the keys/values we want to keep.
        # We could split the method into a superclass
        # method for Webware/WebwareExperimental and a subclass for Cheetah.
        # The superclass would merely 'return dic'.  The subclass would
        # 'dic = super(ThisClass, self).webInput(names, namesMulti, ...)'
        # and then the code below.
        if debug:
           print "<PRE>\n" + pprint.pformat(dic) + "\n</PRE>\n\n"
        self.searchList().insert(0, dic)
        return dic

T = Template   # Short and sweet for debugging at the >>> prompt.

# vim: shiftwidth=4 tabstop=4 expandtab
