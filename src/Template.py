#!/usr/bin/env python
# $Id: Template.py,v 1.9 2001/07/13 22:52:01 tavis_rudd Exp $
"""Provides the core Template class for Cheetah
See the docstring in __init__.py and the User's Guide for more information

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.9 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2001/07/13 22:52:01 $
""" 
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.9 $"[11:-2]


##################################################
## DEPENDENCIES ##

import os                         # used to get environ vars, etc.
import sys                        # used in the error handling code
import re                         # used to define the internal delims regex
import new                        # used to bind the compiled template code
import types                      # used in the mergeNewTemplateData method
import time                       # used in the cache refresh code
from time import time as currentTime # used in the cache refresh code

# intra-package imports ...
from SettingsManager import SettingsManager
from NameMapper import valueForName
import NameMapper
from SearchList import SearchList
import CodeGenerator as CodeGen
from PlaceholderProcessor import PlaceholderProcessor
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
    cacheDirectiveProcessor = CodeGen.CacheDirectiveProcessor()
    endCacheDirectiveProcessor = CodeGen.EndCacheDirectiveProcessor()

    _settings = {
        'useAutocalling': True,
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
                          ('lazyMacroCalls',
                           CodeGen.preProcessLazyMacroCalls),
                          ('lazyMacroCalls',
                           CodeGen.preProcessLazyMacroCalls),
                          ('explicitMacroCalls',
                           CodeGen.preProcessExplicitMacroCalls),
                          ('comments',
                           CodeGen.preProcessComments),
                          ('rawDirectives',
                           CodeGen.preProcessRawDirectives),
                          ('setDirectives',
                           setDirectiveProcessor.preProcess),
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
                          ('placeholders',
                           placeholderProcessor.preProcess),
                          ('unescapePlaceholders',
                           lambda obj, TD: TD.replace(r'\$','$') ),
                          ],
                 
        'tagProcessors':{'placeholders':placeholderProcessor,
                         'displayLogic':displayLogicProcessor,
                         'setDirective':setDirectiveProcessor,
                         'cacheDirective':cacheDirectiveProcessor,
                         'endCacheDirective':endCacheDirectiveProcessor,
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

    def __init__(self, templateDef, *searchList, **kw):
        """setup the namespace search list, process settings, then call
        self._startServer() to parse/compile the template and prepare the
        self.__str__() and self.respond() methods for serving the template.

        If the environment var CHEETAH_DEBUG is set to True the internal
        debug setting will also be set to True."""
        
        self._searchList = SearchList( searchList )
        self._searchList.append(self)
        if kw.has_key('searchList'):
            self._searchList.extend( kw['searchList'] )

        if kw.has_key('macros'):
            self._macros = kw['macros']
            
        if kw.has_key('cheetahBlocks'):
            self._cheetahBlocks = kw['cheetahBlocks']
        else:
            self._cheetahBlocks = {}

        self.initializeSettings()
        if kw.has_key('settings'):
            self.updateSettings(kw['settings'])
            
        if kw.has_key('overwriteSettings'):
            self._settings = kw['overwriteSettings']

        if os.environ.get('CHEETAH_DEBUG'):
            self._settings['debug'] = True
            
        if kw.has_key('plugins'):
            self._settings['plugins'] += kw['plugins']
            for plugin in self._settings['plugins']:
                self.registerServerPlugin(plugin)

        self._templateDef = str( templateDef )

        if not self._settings['delayedStart']:
            self.startServer()
                   
    def searchList(self):
        return self._searchList
    
    def addToSearchList(self, object, restart=True):
        self._searchList.append(object)
        if restart:
            self.startServer()

    def translatePlaceholderVars(self, string, executeCallables=False):
        
        translated = self.placeholderProcessor.translateRawPlaceholderString(
            string, searchList=self.searchList(), templateObj=self,
            executeCallables=executeCallables)
        return translated

    def startServer(self):
        """Process and parse the template, then compile it into a function definition
        that is bound to self.__str__() and self.respond()"""
        
        self._errorMsgStack = []
        generatedFunction = self._codeGenerator( self._templateDef )
        self.__str__ = self._bindFunctionAsMethod( generatedFunction )
        self.respond = self._bindFunctionAsMethod( generatedFunction )
        
        if not self._settings['keepCodeGeneratorResults']:
            self._codeGeneratorResults = {}       

    def _codeGenerator(self, templateDef):
        
        """parse the template definition, generate a python code string from it,
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
        """merge the newDataDict into self.__dict__. This is a recursive merge
        that handles nested dictionaries in the same way as
        Template.updateServerSettings()"""
        
        for key, val in newDataDict.items():
            if type(val) == types.DictType and hasattr(self,key) \
               and type(getattr(self,key)) == types.DictType:
                
                setattr(self,key, mergeNestedDictionaries(getattr(self,key), val))
            else:
                setattr(self,key,val)
   
    def registerServerPlugin(self, plugin):
        """register a plugin that extends the functionality of the Template"""
        plugin.bindToTemplateServer(self)
        
    def _bindFunctionAsMethod(self, function):
        """used to dynamically bind a plain function as a method of the
        Template instance"""
        return new.instancemethod(function, self, self.__class__)

    def _tagProcessor(self, tag):
        """an abstract tag processor that will identify the tag type from its
        tagToken prefix and call the appropriate processor for that type of
        tag"""
        settings = self._settings
        tagToken, tag = tag.split(settings['tagTokenSeparator'])
        processedTag = settings['tagProcessors'][tagToken].processTag(self, tag)
        return processedTag

    
    def _setTimedRefresh(self, translatedTag, interval):
        self._checkForCacheRefreshes = True
        searchList = self.searchList()
        tagValue = eval(translatedTag)
        self._timedRefreshCache[translatedTag] = str(tagValue)
        nextUpdateTime = currentTime() + interval * 60 
        self._timedRefreshList.append(
            [nextUpdateTime, translatedTag, interval])


    def _timedRefresh(self, currTime):
        """refresh all the cached NameMapper vars that are scheduled for a
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
        """  """            
        self._cheetahBlocks[blockName]= blockContents

    def killTemplateBlock(self, *blockNames):
        """ """
        if not hasattr(self, '_blocks'):
            return False
        for blockName in blockNames:
            self._blocks[blockName]= ''

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


    def extendTemplate(self, extension):
        """
        @@needs documenting
        #redefine and #data directives MUST NOT be nested!!
        """
        import re
        
        if not hasattr(self, '_blocks'):
            self._blocks = {}

        redefineDirectiveRE = re.compile(
            r'(?<!#)#redefine[\t ]+' +
            r'(?P<blockName>[A-Za-z_][A-Za-z_0-9]*?)' +
            r'(?:/#|\r\n|\n|\Z)',re.DOTALL)
                                         
        while redefineDirectiveRE.search(extension):
            startTagMatch = redefineDirectiveRE.search(extension)
            blockName = startTagMatch.group('blockName')
            endTagRE = re.compile(r'#end redefine[\t ]+' + blockName + r'[\t ]*(?:/#|\r\n|\n|\Z)',
                                  re.DOTALL | re.MULTILINE)
            endTagMatch = endTagRE.search(extension)
            blockContents = extension[startTagMatch.end() : endTagMatch.start()]
            self.defineTemplateBlock(blockName, blockContents)
            extension = extension[0:startTagMatch.start()] + \
                        extension[endTagMatch.end():]
                   
        ## process the #data and #macro definition directives
        # after removing comments
        extension = CodeGen.preProcessComments(self, extension)
        CodeGen.preProcessDataDirectives(self, extension)
        CodeGen.preProcessMacroDirectives(self, extension) 
   

    ## utility functions ##
    def translatePath(self, path):
        """A hook to enable proper handling of server-side paths with Webware """
        return path
    
    def getFileContents(self, fileName):
        fp = open(fileName,'r')
        output = fp.read()
        fp.close()
        return output
        
    def runAsMainProgram(self):
        """An abstract method that can be reimplemented to enable the Template
        to function as a standalone command-line program for static page
        generation and testing/debugging.

        The debugging facilities are provided by a plugin to Template."""
        
        print self
