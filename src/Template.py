#!/usr/bin/env python
# $Id: Template.py,v 1.45 2001/08/16 23:28:01 tavis_rudd Exp $
"""Provides the core Template class for Cheetah
See the docstring in __init__.py and the User's Guide for more information

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.45 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2001/08/16 23:28:01 $
""" 
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.45 $"[11:-2]


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
from SettingsManager import SettingsManager # baseclass for Template
from Parser import Parser, processTextVsTagsList # baseclass for Template + util func
from Utilities import mergeNestedDictionaries 
from NameMapper import valueFromSearchList, valueForName # this is used in the generated code
import ErrorHandlers              # for the code-generator
import ErrorCheckers              # for placeholder tags
import Formatters

#coreTagProcessors
from PlaceholderProcessor import PlaceholderProcessor
from DisplayLogic import DisplayLogic
from SetDirective import SetDirective
from CacheDirective import CacheDirective, EndCacheDirective
from StopDirective import StopDirective
from FormatterDirective import FormatterDirective

#preProcessing only TagProcessors
from CommentDirective import CommentDirective
from SlurpDirective import SlurpDirective
from RawDirective import RawDirective
from DataDirective import DataDirective
from IncludeDirective import IncludeDirective
from BlockDirective import BlockDirective
from MacroDirective import MacroDirective, \
     LazyMacroCall, CallMacroDirective

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
    
class Template(SettingsManager, Parser):
    """The core template engine: parses, compiles, and serves templates."""
    _settings = {
        'formatter':None,         # string - which formatter from Cheetah.Formatters
        'formatterClass':None,    # class that overrides the 'formatter' setting
        'errorChecker':None,      # string - which errorChecker from Cheetah.ErrorCheckers
        'errorCheckerClass': None,# class that overrides the 'errorChecker' setting
        
        'placeholderStartToken':'$',
        'directiveStartToken':'#',
        'directiveEndToken':'/#',
        'singleLineComment':'##',
        'multiLineComment':('#*','*#'),

        'delayedCompile': False,  # if True, then __init__ won't compile auto-Template
        'plugins':[],
        'useAutocalling': True,
        'debug': False,          

        'includeBlockMarkers': False,   # should output from #block's be wrapped in a comment
        'blockMarkerStart':('<!-- START BLOCK: ',' -->'),
        'blockMarkerEnd':('<!-- END BLOCK: ',' -->'),
        
        ## The rest of this stuff is mainly for internal use
        'placeholderMarker':' placeholderTag.', # the space is intentional!
        'internalDelims':["<Cheetah>","</Cheetah>"],
        'tagTokenSeparator': '__@__',
        'indentationStep': ' '*4, # 4 spaces - used in the generated code
        'initialIndentLevel': 2,  # 1 for def respond(): -- 1 for try:
                                
        'codeGenErrorHandler':ErrorHandlers.CodeGeneratorErrorHandler,
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
        
        SettingsManager.__init__(self)
        
        ## Read in the Template Definition
        #  unravel whether the user passed in a string, filename or file object.
        self._filePath = None
        self._fileMtime = None
        file = kw.get('file', None)
        if templateDef and file:
            raise TypeError("cannot specify both Template Definition and file")
        elif (not templateDef) and (not file):
            raise("must pass Template Definition string, or 'file' keyword arg")
        elif templateDef:   # it's a string templateDef
            pass
        elif type(file) == types.StringType: # it's a filename.
            file = self.normalizePath(file)
            f = open(file) # Raises IOError.
            templateDef = f.read()
            f.close()
            self._filePath = file
            self._fileMtime = os.path.getmtime(file)
            ## @@ add the code to do file modification checks and updates
            
        elif hasattr(file, 'read'):
            templateDef = file.read()
            # Can't set filename or mtime--they're not accessible.
        else:
            raise TypeError("'file' argument must be a filename or file-like object")


        self._templateDef = str( templateDef )
        # by converting to string here we allow objects such as other Templates
        # to be passed in

        ## process the settings
        if kw.has_key('overwriteSettings'):
            # this is intended to be used internally by Nested Templates in #include's
            self._settings = kw['overwriteSettings']
        elif kw.has_key('settings'):
            self.updateSettings(kw['settings'])
           
        if os.environ.get('CHEETAH_DEBUG'):
            self._settings['debug'] = True
       
        ## Setup the searchList of namespaces in which to search for $placeholders
        # + setup a dict of #set directive vars - include it in the searchList
        self._setVars = {}

        if kw.has_key('setVars'):
            # this is intended to be used internally by Nested Templates in #include's
            self._setVars = kw['setVars']
            
        if kw.has_key('preBuiltSearchList'):
            # happens with nested Template obj creation from #include's
            self._searchList = list(kw['preBuiltSearchList'])
        else:
            # create our own searchList
            self._searchList = list(searchList)
            self._searchList.insert(0, self._setVars)
            self._searchList.append( self )
            if kw.has_key('searchList'):
                tup = tuple(kw['searchList'])
                self._searchList.extend(tup) # .extend requires a tuple.

        self._errorMsgStack = []
        self._localVarsList = []   # used to track vars from #set and #for
        self._timedRefreshCache = {} # caching timedRefresh vars
        self._timedRefreshList = []
        self._checkForCacheRefreshes = False
        self._perResponseSetupCodeChunks = {}
        self._rawTextBlocks ={}
        self._rawIncludes = {}
        self._parsedIncludes = {}
        
        ## deal with other keywd args 
        # - these are for internal use by Nested Templates in #include's
        if not hasattr(self, '_macros'):
            self._macros = {}
        
        if kw.has_key('macros'):
            self._macros = kw['macros']

        if kw.has_key('cheetahBlocks'):
            self._cheetahBlocks = kw['cheetahBlocks']
        else:
            self._cheetahBlocks = {}

        ## hook for calculated settings before the tagProcessors have been setup 
        self._initializeSettings()

        ## Setup the Parser base-class
        Parser.__init__(self) # do this before calling self._setupTagProcessors()

        ## create theFormatters dict now for storing refs to the formatter functions
        if self.setting('formatter') and not self.setting('formatterClass'):
            try:
                klass = getattr(Formatters, self.setting('formatter'))
                self.setSetting('formatterClass', klass)
            except:
                ## @@once we've implemented the error-logging framework implement this
                pass

        self._theFormatters = {}
        if self.setting('formatterClass'):
            self._initialFormatter = self.setting('formatterClass')(self)
        else:
            self._initialFormatter = str
            
        self._theFormatters['initial'] = self._initialFormatter


        ## handle 'errorChecker' if neccessary
        if self.setting('errorChecker') and not self.setting('errorCheckerClass'):
            try:
                klass = getattr(ErrorCheckers, self.setting('errorChecker'))
                self.setSetting('errorCheckerClass', klass)
            except:
                ## @@once we've implemented the error-logging framework implement this
                pass

        if self.setting('errorCheckerClass'):
            errorChecker = self.setting('errorCheckerClass')(self)
            self._errorChecker = errorChecker
        else:
            self._errorChecker = None

        ## register the Plugins after everything else has been done, but
        #  before the template has been compiled.
        for plugin in self._settings['plugins']:
            self._registerCheetahPlugin(plugin)

        ## Setup the various TagProcessors
        self._setupTagProcessors()

        ## hook for calculated settings after the tagProcessors have been setup 
        self._finalizeSettings()       

        ## Now, start compile if we're meant to
        if not self.setting('delayedCompile'):
            self.compileTemplate()
        
    def compileTemplate(self):
        """Process and parse the template, then compile it into a function definition
        that is bound to self.__str__() and self.respond()"""
                        
        generatedFunction = self._codeGenerator( self._templateDef )
        self.__str__ = self._bindFunctionAsMethod( generatedFunction )
        self.respond = self._bindFunctionAsMethod( generatedFunction )
        
        if not self._settings['debug']:
            del self._codeGeneratorResults
            del self._templateDef
            self._cheetahBlocks.clear()
            # but don't delete self._generatedCode

    def recompileFromFile(self, path):
        
        """Get an updated templateDef from the specified file. This method is
        used when a file the templateObj is bound to is updated."""

        path = self.normalizePath(path)
        f = open(path) # Raises IOError.
        self._templateDef = f.read()
        f.close()
        self._filePath = path
        self._fileMtime = os.path.getmtime(path)
        self.compileTemplate()
        
    ##################################################
    ## internal methods -- not to be called by end-users
            
    def _finalizeSettings(self):
        """A hook for calculated settings. This method is called by
        self.compileTemplate() after it calls self._setupTagProcessors().
        It should always be called by subclasses.

        If you want to do calculated settings before self._setupTagProcessors()
        use self._initializeSettings()."""
        
        pass

    def _setupTagProcessors(self):
        """Setup the tag processors."""
        
        commentDirective = CommentDirective(self)
        slurpDirective = SlurpDirective(self)
        rawDirective = RawDirective(self)
        includeDirective = IncludeDirective(self)
        blockDirective = BlockDirective(self)
        dataDirective = DataDirective(self)
        macroDirective = MacroDirective(self)
        callMacroDirective = CallMacroDirective(self)
        lazyMacroCall = LazyMacroCall(self)
        
        placeholderProcessor =  PlaceholderProcessor(self)
        displayLogic = DisplayLogic(self)
        setDirective = SetDirective(self)        
        stopDirective = StopDirective(self)
        cacheDirective = CacheDirective(self)
        endCacheDirective = EndCacheDirective(self)
        formatterDirective = FormatterDirective(self)
        
        ##store references to them in a dict
        self._processors = {}
        self._processors.update(locals())
        del self._processors['self']
               
        self._codeGenSettings = {
            'preProcessors': [('rawDirective',
                               rawDirective),
                              ('comment',
                               commentDirective),
                              ('setDirective',
                               setDirective),
                              ('dataDirective',
                               dataDirective),
                              ('blockDirective',
                               blockDirective),
                              ('macroDirective',
                               macroDirective),

                              # do includes before macro calls
                              ('includeDirective',
                               includeDirective),

                              ('lazyMacroCall',
                               lazyMacroCall),
                              ('CallMacro',
                               callMacroDirective),
                              ('lazyMacroCall', # check again after #callMacro directive
                               lazyMacroCall),
                             
                              ('rawDirective',
                               rawDirective),
                              ('comments',
                               commentDirective),
                              ('setDirective',
                               setDirective),
                              # + do includes after macro calls
                              ('includeDirective',
                               includeDirective),
                              
                              ('cacheDirective',
                               cacheDirective),
                              ('endCacheDirective',
                               endCacheDirective),
                              ('slurpDirective',
                               slurpDirective),
                              ('display logic directives',
                               displayLogic),
                              ('stop directives',
                               stopDirective),
                              ('formatterDirective',
                              formatterDirective),
                              ('placeholders',
                               placeholderProcessor),
                              ],
            
            'coreTagProcessors':{'placeholders':placeholderProcessor,
                                 'displayLogic':displayLogic,
                                 'setDirective':setDirective,
                                 'cacheDirective':cacheDirective,
                                 'endCacheDirective':endCacheDirective,
                                 'stopDirective':stopDirective,
                                 'formatterDirective':formatterDirective,
                                 },
            
            'generatedCodeFilters':[],
            }
        
        #end of self._setupTagProcessors()

    def _cleanupProcessors(self):
        
        """Cleanup after the tag processors.  Don't call this before shutdown if
        you want to be able to recompile with a new templateDef or monitor for
        file updates."""
        
        for key, processor in self._processors.items():
            processor.shutdown()
        self._processors.clear()

    
    def _codeGenerator(self, templateDef):
        
        """Parse the template definition, generate a python code string from it,
        then execute the code string to create a python function which can be
        bound as a method of the Template.  Returns a reference to the function.
        
        stage 1 - the raw template is filtered using the pre-processors
        specified in the TemplateServer settings

        stage 2 - convert the $placeholder tags, display logic directives, #set
        directives, #cache diretives, etc. (all the internal-state dependent
        tags) into chunks of python code

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
        codeGenSettings = self._codeGenSettings
        
        state['currFormatterID'] = 'initial'
        if not self._theFormatters['initial'] == str:
            state['interactiveFormatter'] = True
        else:
            state['interactiveFormatter'] = False
                       
        try:
            ## stage 1 - preProcessing of the template string ##
            stage = 1
            if debug: results['stage1'] = []
            for name, preProcessor in codeGenSettings['preProcessors']:
                assert hasattr(preProcessor, 'preProcess'), \
                       'The Processor class ' + name + ' is not valid.'
                templateDef = preProcessor.preProcess(templateDef)
                    
                if isinstance(templateDef, RESTART):
                    # a parser restart might have been requested for direct #include's 
                    return self._codeGenerator(templateDef.data)
                if debug: results['stage1'].append((name, templateDef))

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
            for processor in codeGenSettings['coreTagProcessors'].values():
                processor.initializeTemplateObj()
                
            # b)
            subStage = 'b'
            chunks = templateDef.split(settings['internalDelims'][0])
            textVsTagsList = []
            for chunk in chunks:
                textVsTagsList.extend(chunk.split(settings['internalDelims'][1]))

            for i in range(0,len(textVsTagsList),2):
                ## ''' must be escaped in the text chunks
                textVsTagsList[i] = textVsTagsList[i].replace("'''",r"\'\'\'")
            if debug:
                results['stage2'].append(('textVsTagsList', textVsTagsList))
            
            # c)
            subStage = 'c'
            codePiecesFromTextVsTagsList = processTextVsTagsList(
                textVsTagsList,
                self._coreTagProcessor)
            
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
                          "def generatedFunction(self, trans=None, iAmNested=False," + \
                          "getmtime=os.path.getmtime,\n " + \
                          "filePath=self._filePath,\n " + \
                          "fileMtime=self._fileMtime,\n " + \
                          "format=self._initialFormatter,\n " + \
                          "searchList=self._searchList, " + \
                          "setVars=self._setVars,\n " + \
                          "checkForCacheRefreshes=self._checkForCacheRefreshes, " + \
                          "timedRefreshCache=self._timedRefreshCache,\n " + \
                          "timedRefreshList=self._timedRefreshList, " + \
                          "timedRefresh=self._timedRefresh,\n " + \
                          "errorChecker=self._errorChecker" + \
                          "):\n" \
                          + indent * 1 + "try:\n" \
                          + indent * 2 + "#setupCodeInsertMarker\n" \
                          + indent * 2 + "if filePath and getmtime(filePath) > fileMtime:\n"\
                          + indent * 3 + "self.recompileFromFile(filePath)\n"\
                          + indent * 3 + "return self.respond(trans=trans, iAmNested=iAmNested)\n"\
                          + indent * 2 + "if checkForCacheRefreshes:\n"\
                          + indent * 3 + "currTime = currentTime()\n"\
                          + indent * 3 + "timedRefreshList.sort()\n"\
                          + indent * 3 + "if currTime >= timedRefreshList[0][0]:\n"\
                          + indent * 4 + "timedRefresh(currTime)\n"\
                          + indent * 3 + "                                   \n" \
                          + indent * 2 + "outputList = []\n" \
                          + indent * 2 + "outputList.extend( ['''" + \
                                         codeFromTextVsTagsList + \
                                         "''',] )\n" \
                          + indent * 2 + "output = ''.join(outputList)\n" \
                          + indent * 2 + "if trans and not iAmNested:\n" \
                          + indent * 3 + "trans.response().write(output)\n" \
                          + indent * 2 + "return output\n" \
                          + indent * 1 + "except:\n" \
                          + indent * 2 + "print self._settings['responseErrorHandler'](self)\n" \
                          + indent * 2 + "raise\n" \

            
            perResponseSetupCode = ''
            for tagProcessor, codeChunk in self._perResponseSetupCodeChunks.items():
                perResponseSetupCode += codeChunk
            def insertCode(match, perResponseSetupCode=perResponseSetupCode):
                return match.group() + perResponseSetupCode
            generatedCode = re.sub(r'#setupCodeInsertMarker\n', insertCode , generatedCode)

            if debug: results['stage3'].append( ('generatedCode', generatedCode) )

            
            ## stage 4 - final filtering of the generatedCode  ##
            # - this is an unused hook as of Aug 2001
            stage = 4
            if debug: results['stage4'] = []
            for filter in codeGenSettings['generatedCodeFilters']:
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
            ## call codeGenErrorHandler, which in turn calls the ErrorHandler ##
            # for the stage in which the error occurred
            print settings['codeGenErrorHandler'](self)
            
            self._cleanupProcessors()  
            #self.shutdown() #@@ should we cleanup after an exception?
            
            raise          


    def _coreTagProcessor(self, tag):
        """An abstract tag processor that will identify the tag type from its
        tagToken prefix and call the appropriate processor for that type of tag.
        This used for the core tags that are sensitive to state values such as
        the indentation level."""
        
        tagToken, tag = tag.split(self.setting('tagTokenSeparator'))
        processedTag = self._codeGenSettings['coreTagProcessors'][tagToken].processTag(tag)
        return processedTag

    def _state(self):
        """Return a reference to self._codeGeneratorState. This is for internal
        use by the tag processors only."""
        
        return self._codeGeneratorState
   
    def _registerCheetahPlugin(self, plugin):
        
        """Register a plugin that extends the functionality of the Template.
        This method is called automatically by them __init__() method and should
        not be called by end-users."""
        
        plugin(self)
        
    def _bindFunctionAsMethod(self, function):
        """Used to dynamically bind a plain function as a method of the
        Template instance"""
        return new.instancemethod(function, self, self.__class__)
        
    def _setTimedRefresh(self, ID, translatedTag, interval):
        """Setup a cache refresh for a $*[time]*placeholder."""
        self._checkForCacheRefreshes = True
        tagValue = self.evalPlaceholderString(translatedTag)
        self._timedRefreshCache[ID] = str(tagValue)
        nextUpdateTime = currentTime() + interval * 60 
        self._timedRefreshList.append(
            [nextUpdateTime, translatedTag, interval, ID])


    def _timedRefresh(self, currTime):
        """Refresh all the cached NameMapper vars that are scheduled for a
        refresh at this time, and reschedule them for their next update.

        the entries in the recache list are in the format [nextUpdateTime, name,
        interval, ID] """

        refreshList = self._timedRefreshList
        for i in range(len(refreshList)):
            if refreshList[i][0] < currTime:
                translatedTag = refreshList[i][1]
                interval = refreshList[i][2]
                ID = refreshList[i][3]
                self._setTimedRefresh(ID, translatedTag, interval)
                del refreshList[i]
                refreshList.sort()


    ##################################################
    ## methods that can only be used before a template has been compiled
                
    def defineTemplateBlock(self, blockName, blockContents):
        """Define a block.  See the user's guide for info on blocks.  Only call
        this method before the template has been Compiled."""
        
        self._cheetahBlocks[blockName]= blockContents

    # make an alias
    redefineTemplateBlock = defineTemplateBlock
    
    def killTemplateBlock(self, *blockNames):
        
        """Fill a block with an empty string so it won't appear in the filled
        template output. Only call this method before the template has been
        compiled."""
        
        for blockName in blockNames:
            self._cheetahBlocks[blockName]= ''

    def loadMacro(self, macroName, macro):
        
        """Load a macro into the macros dictionary, using the specified
        macroName.  Only call this method before the template has been
        compiled."""
        
        if not hasattr(self, '_macros'):
            self._macros = {}

        self._macros[macroName] = macro

    def loadMacros(self, *macros):
        
        """Create macros from any number of functions and/or bound methods.  For
        each macro, the function/method name is used as the macro name. Only
        call this method before the template has been compiled."""
        
        if not hasattr(self, '_macros'):
            self._macros = {}

        for macro in macros:
            self.loadMacro(macro.__name__, macro)
        
    def loadMacrosFromModule(self, module):
        
        """Load all the macros from a module into the macros dictionary. Only
        call this method before the template has been compiled."""
        
        if not hasattr(self, '_macros'):
            self._macros = {}

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

        Only call this method before the template has been Compiled."""
        
        bits = self._directiveREbits

        redefineDirectiveRE = re.compile(
            bits['start'] + r'redefine[\f\t ]+' +
            r'(?P<blockName>[A-Za-z_][A-Za-z_0-9]*?)' +
            bits['endGrp'],re.DOTALL)
                                         
        while redefineDirectiveRE.search(extensionStr):
            startTagMatch = redefineDirectiveRE.search(extensionStr)
            blockName = startTagMatch.group('blockName')
            endTagRE = re.compile(bits['startTokenEsc'] +
                                  r'end redefine[\t ]+' + blockName +
                                  r'[\f\t ]*' + bits['endGrp'],
                                  re.DOTALL | re.MULTILINE)
            endTagMatch = endTagRE.search(extensionStr)
            blockContents = extensionStr[startTagMatch.end() : endTagMatch.start()]
            self.defineTemplateBlock(blockName, blockContents)
            extensionStr = extensionStr[0:startTagMatch.start()] + \
                        extensionStr[endTagMatch.end():]
                   
        ## process the #data and #macro definition directives
        # after removing comments
        extensionStr = self._processors['commentDirective'].preProcess(extensionStr)
        self._processors['dataDirective'].preProcess(extensionStr)
        self._processors['macroDirective'].preProcess(extensionStr) 


    ##################################################
    ## methods that can be called at any time
        
    def searchList(self):
        """Return a reference to the searchlist"""
        return self._searchList
    
    def addToSearchList(self, object):
        """Append an object to the end of the searchlist.""" 
        self._searchList.append(object)

    def errorChecker(self):
        """Return a reference to the errorChecker"""
        return self._errorChecker

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


    def shutdown(self):
        """Make sure all reference cycles have been broken this object is
        deleted. """
        self._cleanupProcessors()
        
        for key in dir(self):
            setattr(self, key, None)
            delattr(self, key)


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
            
    
    def runAsMainProgram(self):
        """An abstract method that can be reimplemented to enable the Template
        to function as a standalone command-line program for static page
        generation and testing/debugging.

        The debugging facilities will be provided by a plugin to Template, at
        some later date."""
        
        print self
