#!/usr/bin/env python
# $Id: Template.py,v 1.20 2001/08/07 19:42:12 tavis_rudd Exp $
"""Provides the core Template class for Cheetah
See the docstring in __init__.py and the User's Guide for more information

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.20 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2001/08/07 19:42:12 $
""" 
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.20 $"[11:-2]


##################################################
## DEPENDENCIES ##

import os                         # used to get environ vars, etc.
import sys                        # used in the error handling code
import re                         # used to define the internal delims regex
import new                        # used to bind the compiled template code
import types                      # used in the mergeNewTemplateData method
import time                       # used in the cache refresh code
from time import time as currentTime # used in the cache refresh code
import types                      # used in the constructor
import os.path                    # used in Template.normalizePath()

# intra-package imports ...
from SettingsManager import SettingsManager
from NameMapper import valueForName
import NameMapper
from SearchList import SearchList
import CodeGenerator as CodeGen
from PlaceholderProcessor import PlaceholderProcessor
from CacheDirectiveProcessor import CacheDirectiveProcessor, EndCacheDirectiveProcessor
from StopDirectiveProcessor import StopDirectiveProcessor
import ErrorHandlers
from Delimiters import delimiters as delims
from Utilities import \
     removeDuplicateValues, \
     mergeNestedDictionaries, \
     insertLineNums

##################################################
## CONSTANTS & GLOBALS ##

True = (1==1)
False = (0==1)

##################################################
## CLASSES ##

class Error(Exception):
    pass

class RESTART:
    """A token class that the #include directive can use to signal that the
    codeGenerator needs to restart and parse new stuff that has been included"""
    
    def __init__(self, templateDef):
        self.data = templateDef
    
class Template(SettingsManager):
    """The core template engine: parses, compiles, and serves templates."""

    placeholderProcessor =  PlaceholderProcessor()
    displayLogicProcessor = CodeGen.DisplayLogicProcessor()
    setDirectiveProcessor = CodeGen.SetDirectiveProcessor()        
    stopDirectiveProcessor = StopDirectiveProcessor()
    cacheDirectiveProcessor = CacheDirectiveProcessor()
    endCacheDirectiveProcessor = EndCacheDirectiveProcessor()

    _settings = {
        'placeholderStartToken':'$',
        'useAutocalling': True,
        'useLateBinding': True,
        'delayedStart': False,            
        'plugins':[],
        'varNotFound_handler': CodeGen.varNotFound_echo,
        'debug': False,
        'keepCodeGeneratorResults': False,
        'blockMarkerStart':['<!-- START BLOCK: ',' -->'],
        'blockMarkerEnd':['<!-- END BLOCK: ',' -->'],
        'includeBlockMarkers': False,


        'delimiters':{'includeDirective': [delims['includeDirective_gobbleWS'],
                                           delims['includeDirective'],
                                           ],
                      'dataDirective': [delims['dataDirective_gobbleWS'],
                                        delims['dataDirective'],
                                        ],
                      'macroDirective': [delims['macroDirective'],
                                         ],
                      'blockDirectiveStart': [delims['blockDirectiveStart_gobbleWS'],
                                              delims['blockDirectiveStart'],
                                              ],
                      'lazyMacroCalls': [delims['lazyMacroCalls'],],
                      'callMacro': [delims['callMacro'],],
                      'callMacroArgs': delims['callMacroArgs'],
                      'rawDirective': [delims['rawDirective'],],
                      'comments': [delims['multiLineComment'],
                                   delims['singleLineComment']],
                      'slurp': [delims['slurpDirective_gobbleWS'],
                                delims['slurpDirective'],
                                ],
                      },
       
        'internalDelims':["<Cheetah>","</Cheetah>"],
        'internalDelimsRE': re.compile(r"<Cheetah>(.+?)</Cheetah>",
                                     re.DOTALL),
        'tagTokenSeparator': '__@__',
        'indentationStep': ' '*4, # 4 spaces - used in the generated code
        'initialIndentLevel': 2, 
            
        'preProcessors': [('rawDirectives',
                           CodeGen.preProcessRawDirectives),
                          ('comments',
                           CodeGen.preProcessComments),
                          ('setDirectives',
                           setDirectiveProcessor.preProcess),
                          ('dataDirectives',
                           CodeGen.preProcessDataDirectives),
                          ('blockDirectives',
                           CodeGen.preProcessBlockDirectives),
                          ('macroDirectives',
                           CodeGen.preProcessMacroDirectives),

                          # do includes before macro calls
                          ('includeDirectives',
                           CodeGen.preProcessIncludeDirectives),

                          ('lazyMacroCalls',
                           CodeGen.preProcessLazyMacroCalls),
                          ('lazyMacroCalls',
                           CodeGen.preProcessLazyMacroCalls),
                          ('explicitMacroCalls',
                           CodeGen.preProcessExplicitMacroCalls),

                          ('rawDirectives',
                           CodeGen.preProcessRawDirectives),
                          ('comments',
                           CodeGen.preProcessComments),
                          ('setDirectives',
                           setDirectiveProcessor.preProcess),
                          # + do includes after macro calls
                          ('includeDirectives',
                           CodeGen.preProcessIncludeDirectives),

                          ('cacheDirective',
                           cacheDirectiveProcessor.preProcess),
                          ('endCacheDirective',
                           endCacheDirectiveProcessor.preProcess),
                          ('slurpDirectives',
                           CodeGen.preProcessSlurpDirective),
                          ('display logic directives',
                           displayLogicProcessor.preProcess),
                          ('stop directives',
                           stopDirectiveProcessor.preProcess),
                          ('placeholders',
                           placeholderProcessor.preProcess),
                          ('unescapePlaceholders',
                           placeholderProcessor.unescapePlaceholders),
                          ],
                 
        'tagProcessors':{'placeholders':placeholderProcessor,
                         'displayLogic':displayLogicProcessor,
                         'setDirective':setDirectiveProcessor,
                         'cacheDirective':cacheDirectiveProcessor,
                         'endCacheDirective':endCacheDirectiveProcessor,
                         'stopDirective':stopDirectiveProcessor,
                         },
            
                    
        'generatedCodeFilters':[('removeEmptyStrings',
                                 CodeGen.removeEmptyStrings),
                                ('addPerResponseCode',
                                 CodeGen.addPerResponseCode),
                                ],
                    
        'masterErrorHandler':ErrorHandlers.CodeGeneratorErrorHandler,
        'responseErrorHandler': ErrorHandlers.ResponseErrorHandler,

        'stages':{1:{'title':'pre-processing',
                     'description':"the raw template is filtered using\n" + \
                     "the pre-processors specified in the TemplateServer settings.",
                     'errorHandler':ErrorHandlers.Stage1ErrorHandler,
                     },
                  2:{'title':'convert-tags-to-code',
                     'description':"the tags that have been translated to\n" + \
                     "the internal format are converted into chunks of python code.",
                     'errorHandler':ErrorHandlers.Stage2ErrorHandler,
                     },
                  3:{'title':'wrap-code-in-function-definition',
                     'description':"the chunks of python code from stage 2\n" + \
                     "are wrapped up in a code string of a function definition.",
                     'errorHandler':ErrorHandlers.Stage3ErrorHandler,
                     },
                  4:{'title':'filter-generated-code',
                     'description':"the generated code string is filtered\n" + \
                     "using the filters defined in the TemplateServer settings.",
                     'errorHandler':ErrorHandlers.Stage4ErrorHandler,
                     },
                  5:{'title':'execute-generated-code',
                     'description':"the generated code string is executed\n" + \
                     "to produce a function that will be bound as a method " + \
                     "of the TemplateServer.",
                     'errorHandler':ErrorHandlers.Stage5ErrorHandler,
                     },
                  },
        }

    def __init__(self, templateDef=None, *searchList, **kw):
        
        """Read in the template definition, setup the namespace searchList,
        process settings, then call self._compileTemplate() to parse/compile the
        template and prepare the self.__str__() and self.respond() methods for
        serving the template.

        Configuration settings should be passed in as a dictionary via the
        'settings' keyword.
        
        If the environment var CHEETAH_DEBUG is set to True the internal
        debug setting will also be set to True."""
        
        ## Read in the Template Definition
        #  unravel whether the user passed in a string, filename or file object.
        self._fileName = None
        self._fileMtime = None
        file = kw.get('file', None)
        if templateDef and file:
            raise TypeError("cannot specify both Template Definition and file")
        elif (not templateDef) and (not file):
            raise("must pass Template Definition string, or 'file' keyword arg")
        elif templateDef:   # it's a string templateDef
            pass
        elif type(file) == types.StringType: # it's a filename.
            f = open(file) # Raises IOError.
            templateDef = f.read()
            f.close()
            self._fileName = file
            self._fileMtime = os.path.getmtime(file)
            ## @@ add the code to do file modification checks and updates
            
        elif hasattr(file, 'read'):
            templateDef = file.read()
            # Can't set filename or mtime--they're not accessible.
        else:
            raise TypeError("'file' argument must be a filename or file-like object")

        self._templateDef = str( templateDef ) 
        # by converting to string here we allow other objects such as other Templates
        # to be passed in


        ## Setup the searchList of namespaces in which to search for $placeholders 
        self._searchList = SearchList( searchList )
        self._searchList.append(self)
        if kw.has_key('searchList'):
            tup = tuple(kw['searchList'])
            self._searchList.extend(tup) # .extend requires a tuple.


        ## process the settings
        self.initializeSettings()
        if kw.has_key('settings'):
            self.updateSettings(kw['settings'])
        if kw.has_key('overwriteSettings'):
            self._settings = kw['overwriteSettings']
        self.placeholderProcessor.setTagStartToken(self.setting('placeholderStartToken'))

        ## deal with other keywd args
        if kw.has_key('macros'):
            self._macros = kw['macros']
        if kw.has_key('cheetahBlocks'):
            self._cheetahBlocks = kw['cheetahBlocks']
        else:
            self._cheetahBlocks = {}
        if os.environ.get('CHEETAH_DEBUG'):
            self._settings['debug'] = True
        if kw.has_key('plugins'):
            self._settings['plugins'] += kw['plugins']
            for plugin in self._settings['plugins']:
                self._registerServerPlugin(plugin)

        
        if not self._settings['delayedStart']:
            self.compileTemplate()
                   
    def searchList(self):
        """Return a reference to the searchlist"""
        return self._searchList
    
    def addToSearchList(self, object, restart=True):
        """Append an object to the end of the searchlist.""" 
        self._searchList.append(object)
        
        if restart:
            ## @@ change the restart default to False once we implement run-time
            # $placeholder translation.
            self.compileTemplate()

    def translatePlaceholderVars(self, string, executeCallables=False):
        """Translate all the $placeholders in a string to the appropriate Python
        code.  This method is used to translate $placeholders inside directives,
        not for the Template Definition itself."""
        
        translated = self.placeholderProcessor.translateRawPlaceholderString(
            string, searchList=self.searchList(), templateObj=self,
            executeCallables=executeCallables)
        return translated

    def compileTemplate(self):
        """Process and parse the template, then compile it into a function definition
        that is bound to self.__str__() and self.respond()"""
        
        self._errorMsgStack = []
        generatedFunction = self._codeGenerator( self._templateDef )
        self.__str__ = self._bindFunctionAsMethod( generatedFunction )
        self.respond = self._bindFunctionAsMethod( generatedFunction )
        
        if not self._settings['keepCodeGeneratorResults']:
            self._codeGeneratorResults = {}       

    ## make an alias
    recompile = compileTemplate
    
    def _codeGenerator(self, templateDef):
        
        """Parse the template definition, generate a python code string from it,
        then execute the code string to create a python function which can be
        bound as a method of the Template.  Returns a reference to the function.
        
        stage 1 - the raw template is filtered using the pre-processors
        specified in the TemplateServer settings

        stage 2 - convert the $placeholder tags, display logic directives, #set
        directives, #cache diretives, etc. into chunks of python code

        stage 3 - the chunks of python code and the chunks of plain text from
        the 2nd stage are wrapped up in a code string of a function definition

        stage 4 - the generated code string is filtered using the filters
        defined in the TemplateServer settings

        stage 5 - the generated code string is executed to produce a python
        function, that will become a method of the TemplateServer

        These stages are contain in a try: ... except: ... block that will
        provide helpful information for debugging if an error is caught."""
        
        settings = self._settings
        stageSettings = settings['stages']
        debug = settings['debug']
        results = self._codeGeneratorResults = {}
        state = self._codeGeneratorState = {}
        self._localVarsList = []   # used to track vars from #set and #for

        templateDef = templateDef.replace("'''",r"\'\'\'") # ''' must be escaped
        
        try:
            ## stage 1 - preProcessing of the template string ##
            stage = 1
            if debug: results['stage1'] = []
            for preProcessor in settings['preProcessors']:
                templateDef = preProcessor[1](self, templateDef)
                if isinstance(templateDef, RESTART):
                    # a parser restart might have been requested for #include's 
                    return self._codeGenerator(templateDef.data)
                if debug: results['stage1'].append((preProcessor[0], templateDef))

            ## stage 2 - generate the python code for each of the tokenized tags ##
            #  a) initialize this Template Obj for each processor
            #  b) separate internal tags from text in the template to create
            #     textVsTagsList 
            #  c) send textVsTagsList through self._tagTokenProcessor to generate
            #     the code pieces
            #  d) merge the code pieces into a single string
            stage = 2
            if debug: results['stage2'] = []
            
            # a)
            subStage = 'a'
            for processor in settings['tagProcessors'].values():
                processor.initializeTemplateObj(self)
                
            # b)
            subStage = 'b'
            textVsTagsList = CodeGen.separateTagsFromText(
                templateDef, settings['internalDelimsRE'])
            if debug:
                results['stage2'].append(('textVsTagsList', textVsTagsList))
            
            # c)
            subStage = 'c'
            codePiecesFromTextVsTagsList = CodeGen.processTextVsTagsList(
                textVsTagsList,
                self._tagProcessor)
            
            # d)
            subStage = 'd'
            codeFromTextVsTagsList = "".join(codePiecesFromTextVsTagsList)
            if debug:
                results['stage2'].append(('codeFromTextVsTagsList',
                                          codeFromTextVsTagsList))

            ## stage 3 - wrap the code up in a function definition ##
            stage = 3
            if debug: results['stage3'] = []
            indent = settings['indentationStep']
            generatedCode = \
                          "def generatedFunction(self, trans=None, iAmNested=False):\n" \
                          + indent * 1 + "try:\n" \
                          + indent * 2 + "#setupCodeInsertMarker\n" \
                          + indent * 2 + "searchList = self.searchList()\n" \
                          + indent * 2 + "outputList = []\n" \
                          + indent * 2 + "outputList.extend( ['''" + \
                                         codeFromTextVsTagsList + \
                                         "''',] )\n" \
                          + indent * 2 + "output = ''.join(outputList)\n" \
                          + indent * 2 + "if trans and not iAmNested:\n" \
                          + indent * 3 + "trans.response().write(output)\n" \
                          + indent * 2 + "return output\n" \
                          + indent * 1 + "except:\n" \
                          + indent * 2 + "print self._settings['responseErrorHandler']()\n" \
                          + indent * 2 + "raise\n" \
            
            if debug: results['stage3'].append( ('generatedCode', generatedCode) )

            
            ## stage 4 - final filtering of the generatedCode  ##
            stage = 4
            if debug: results['stage4'] = []
            for filter in settings['generatedCodeFilters']:
                generatedCode = filter[1](self, generatedCode)
                if debug: results['stage4'].append( (filter[0], generatedCode) )

            ## stage 5 - create "generatedFunction" in this namespace ##
            stage = 5
            if debug: results['stage5'] = []
            exec generatedCode
            if debug:
                results['stage5'].append(('generatedFunction', generatedFunction))
            
            ##
            self._generatedCode = generatedCode
            
            return generatedFunction
                
        except:
            ## call masterErrorHandler, which in turn calls the ErrorHandler ##
            # for the stage in which the error occurred
            print settings['masterErrorHandler']()
            raise
            

    def mergeNewTemplateData(self, newDataDict):
        """Merge the newDataDict into self.__dict__. This is a recursive merge
        that handles nested dictionaries in the same way as
        Template.updateServerSettings()"""
        
        for key, val in newDataDict.items():
            if type(val) == types.DictType and hasattr(self,key) \
               and type(getattr(self,key)) == types.DictType:
                
                setattr(self,key, mergeNestedDictionaries(getattr(self,key), val))
            else:
                setattr(self,key,val)
   
    def _registerServerPlugin(self, plugin):
        
        """Register a plugin that extends the functionality of the Template.
        This method is called automatically by __init__() method and should not
        be called by end-users."""
        
        plugin.bindToTemplateServer(self)
        
    def _bindFunctionAsMethod(self, function):
        """Used to dynamically bind a plain function as a method of the
        Template instance"""
        return new.instancemethod(function, self, self.__class__)

    def _tagProcessor(self, tag):
        """An abstract tag processor that will identify the tag type from its
        tagToken prefix and call the appropriate processor for that type of
        tag"""
        settings = self._settings
        tagToken, tag = tag.split(settings['tagTokenSeparator'])
        processedTag = settings['tagProcessors'][tagToken].processTag(self, tag)
        return processedTag

    
    def _setTimedRefresh(self, translatedTag, interval):
        """Setup a cache refresh for a $*[time]*placeholder."""
        self._checkForCacheRefreshes = True
        searchList = self.searchList()
        tagValue = eval(translatedTag)
        self._timedRefreshCache[translatedTag] = str(tagValue)
        nextUpdateTime = currentTime() + interval * 60 
        self._timedRefreshList.append(
            [nextUpdateTime, translatedTag, interval])


    def _timedRefresh(self, currTime):
        """Refresh all the cached NameMapper vars that are scheduled for a
        refresh at this time, and reschedule them for their next update.

        the entries in the recache list are in the format [nextUpdateTime, name,
        interval] """

        refreshList = self._timedRefreshList
        for i in range(len(refreshList)):
            if refreshList[i][0] < currTime:
                translatedTag = refreshList[i][1]
                interval = refreshList[i][2]
                self._setTimedRefresh(translatedTag, interval)
                del refreshList[i]
                refreshList.sort()
       
    def defineTemplateBlock(self, blockName, blockContents):
        """Define a block.  See the user's guide for info on blocks."""            
        self._cheetahBlocks[blockName]= blockContents

    def killTemplateBlock(self, *blockNames):
        """Fill a block with an empty string so it won't appear in the filled
        template output."""
        
        if not hasattr(self, '_cheetahBlocks'):
            return False
        for blockName in blockNames:
            self._cheetahBlocks[blockName]= ''

    def loadMacro(self, macroName, macro):
        """Load a macro into the macros dictionary, using the specified macroName"""
        
        if not hasattr(self, '_macros'):
            self._macros = {}

        self._macros[macroName] = macro


    def loadMacros(self, *macros):
        """Create macros from any number of functions and/or bound methods.  For
        each macro, the function/method name is used as the macro name.  """

        for macro in macros:
            self.loadMacro(macro.__name__, macro)
        
    def loadMacrosFromModule(self, module):
        """Load all the macros from a module into the macros dictionary"""          

        if hasattr(module,'_exclusionList'):
            exclusionList = module._exclusionList
        else:
            exclusionList = ()
            
        macrosList = []
        for obj in module.__dict__.values():
            if callable(obj) and obj not in exclusionList:
                macrosList.append( (obj.__name__, obj) )
            
        for macro in macrosList:
            self.loadMacro(macro[0], macro[1])


    def extendTemplate(self, extensionStr):
        """This method is used to extend an existing Template object with
        #redefine's of the existing blocks.  See the Users' Guide for more
        details on #redefine.  The 'extensionStr' argument should be a string
        that contains #redefine directives.  It can also contain #macro
        definitions and #data directives.

        The #extend directive that is used with .tmpl files calls this method
        automatically, feeding the contents of .tmpl file to this method as
        'extensionStr'.

        #redefine and #data directives MUST NOT be nested!!
        """
        import re
        
        if not hasattr(self, '_blocks'):
            self._blocks = {}

        redefineDirectiveRE = re.compile(
            r'(?<!#)#redefine[\t ]+' +
            r'(?P<blockName>[A-Za-z_][A-Za-z_0-9]*?)' +
            r'(?:/#|\r\n|\n|\Z)',re.DOTALL)
                                         
        while redefineDirectiveRE.search(extensionStr):
            startTagMatch = redefineDirectiveRE.search(extensionStr)
            blockName = startTagMatch.group('blockName')
            endTagRE = re.compile(r'#end redefine[\t ]+' + blockName + r'[\t ]*(?:/#|\r\n|\n|\Z)',
                                  re.DOTALL | re.MULTILINE)
            endTagMatch = endTagRE.search(extensionStr)
            blockContents = extensionStr[startTagMatch.end() : endTagMatch.start()]
            self.defineTemplateBlock(blockName, blockContents)
            extensionStr = extensionStr[0:startTagMatch.start()] + \
                        extensionStr[endTagMatch.end():]
                   
        ## process the #data and #macro definition directives
        # after removing comments
        extensionStr = CodeGen.preProcessComments(self, extensionStr)
        CodeGen.preProcessDataDirectives(self, extensionStr)
        CodeGen.preProcessMacroDirectives(self, extensionStr) 


    ## utility functions ##   
    def normalizePath(self, path):
        """A hook for any neccessary path manipulations.

        For example, when this is used with Webware servlets all relative paths
        must be converted so they are relative to the servlet's directory rather
        than relative to the program's current working dir.

        The default implementation just normalizes the path for the current
        operating system."""
        
        return os.path.normpath(path.replace("\\",'/'))
    
    def getFileContents(self, path):
        """A hook for getting the contents of a file.  The default
        implementation just uses the Python open() function to load local files.
        This method could be reimplemented to allow reading of remote files via
        various protocols, as PHP allows with its 'URL fopen wrapper'"""
        
        fp = open(path,'r')
        output = fp.read()
        fp.close()
        return output
        
    def getUnknowns(self):
        """
        Returns a sorted list of Placeholder Names which are missing in the
        Search List.
        """
        class Accumulator:
            """
            Accumulate unique values.  This is essentially a set class.
            The 'include' method returns '' as a side effect so that it may
            be used as a CodeGenerator.varNotFound_* replacement.
            """
            def __init__(self):
                self.data = {}
            def include(self, templateObj, tag):
                """Add a tag to the set."""
                self.data[tag] = 1
                return ''
            def result(self):
                """Return the list of tags in the set, sorted."""
                ret = self.data.keys()
                ret.sort()
                return ret
        originalHandler = self.setting('varNotFound_handler')
        accum = Accumulator()
        self.setSetting('varNotFound_handler', accum.include)
        try:
            str(self) # Fill the Template Object and throw away the result.
            unknowns = accum.result()
        finally:
            self.setSetting('varNotFound_handler', originalHandler)
        return unknowns
            
    
    def runAsMainProgram(self):
        """An abstract method that can be reimplemented to enable the Template
        to function as a standalone command-line program for static page
        generation and testing/debugging.

        The debugging facilities will be provided by a plugin to Template, at
        some later date."""
        
        print self
