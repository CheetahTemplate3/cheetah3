#!/usr/bin/env python
# $Id: Template.py,v 1.1 2001/06/13 03:50:39 tavis_rudd Exp $
"""Provides the core Template class for Cheetah
See the docstring in __init__.py and the User's Guide for more information

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>,
        with code/advice from Ian Bicking, Mike Orr, Chuck Esterbrook and others
        It was inspired by Chuck's RNV module <echuck@mindspring.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.1 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2001/06/13 03:50:39 $
""" 
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.1 $"[11:-2]


##################################################
## DEPENDENCIES ##

import os                         # used to get environ vars, etc.
import sys                        # used in the error handling code
import new                        # used to bind the compiled template code
import types                      # used in the mergeNewTemplateData method
import time                       # used in the cache refresh code
from time import time as currentTime # used in the cache refresh code

# intra-package imports ...
from SettingsManager import SettingsManager
from NameMapper import valueForName, determineNameType
import NameMapper
import CodeGenerator as CodeGen
import ErrorHandlers
from Delimeters import delimeters as delims
from Utilities import \
     removeDuplicateValues, \
     mergeNestedDictionaries, \
     insertLineNums

##################################################
## CONSTANTS & GLOBALS ##

True = (1==1)
False = (0==1)

EVAL_TAG_TYPE = 0
EXEC_TAG_TYPE = 1


# text descriptions of what each stage in TemplateServer._codeGenerator() does
stageDescriptions = {
1:"""the raw template is filtered using
the pre-processors specified in the TemplateServer settings.""",
2:"""the core tags ($, #set, #if, #for,
<%...%>, and <%=...%>, etc.) are converted to the internal tag format.""",
3:"""the template is filtered for the 2nd
time using the post-processors specified in the TemplateServer settings.""",
4:"""the tags that have been translated to
the internal format are converted into chunks of python code.""",
5:"""the chunks of python code from stage 4
are wrapped up in a code string of a function definition.""",
6:"""the generated code string is filtered
using the filters defined in the TemplateServer settings.""",
7:"""the generated code string is executed
to produce a function that will be bound as a method of the TemplateServer.""",
}


##################################################
## CLASSES ##

class Error(Exception):
    pass

class NoDefault:
    pass

class Template(SettingsManager):
    """The core template engine: parses, compiles, and serves templates."""

    def __init__(self, templateDef, *searchList, **kw):
        """setup the namespace search list, process settings, then call
        self._start() to parse/compile the template and prepare the
        self.__str__() and self.respond() methods for serving the template.

        If the environment var CHEETAH_DEBUG is set to True the internal
        debug setting will also be set to True."""
        
        self._searchList = list(searchList) + [self,]
        if kw.has_key('searchList'):
            self._searchList += kw['searchList']

        self.initializeSettings()
        if kw.has_key('settings'):
            self.updateSettings(kw['settings'])

        if os.environ.get('CHEETAH_DEBUG'):
            self._settings['debug'] = True
            
        if kw.has_key('plugins'):
            self._settings['plugins'] += kw['plugins']
            for plugin in self._settings['plugins']:
                self.registerServerPlugin(plugin)

        self._rawTemplate = str( templateDef )

        if not self._settings['delayedStart']:
            self.startServer()

    
    def initializeSettings(self):
        """create the default settings """

        def includeDirectiveLoop(server, template):
            """process the include Directives recursively and plus all the other
            directives/filters that affect them or are affected by them"""
            settings = server._settings
            extDelimeters = settings['extDelimeters']
            
            regexs = extDelimeters['includeDirective']
            regexs += extDelimeters['macroDirective']
            regexs += extDelimeters['blockDirectiveStart']

            try:
                while filter(None, [regex.search(template) for regex in regexs]):
                    for includeDirectiveRE in extDelimeters['includeDirective']:
                        
                        ## must alternate between the #parse regexes or
                        # whitespace gobbling in  nested #parse blocks
                        # won't be handled properly
                    
                        for processor in \
                            settings['codeGenerator']['includeDirectiveLoop']:
                            
                            template = processor[1](server, template)
                            
                        template = \
                                 CodeGen.preProcessIncludeDirectives(server,
                                                                   template,
                                                                   includeDirectiveRE)                    
                ## do one more final pass
                for processor in settings['codeGenerator']['includeDirectiveLoop']:
                    template = processor[1](server, template)
                    
            except:
                errMsg = '\n'
                errMsg += "\nThe includeDirectiveLoop was processing " + \
                          processor[0] + \
                          " when the error occurred.\n"
                errMsg += "This was the state of the template when the error " +\
                          "occurred:\n\n"
                errMsg += insertLineNums( template ) + '\n'
                server._errorMsgStack.append( errMsg )
                raise

            return template
        
        self._settings = {
            'delayedStart': False,            
            
            'plugins':[],
            'defaultVarValue':None,
            # default val for names, if ==None then varNotFound_handler is called
            'varNotFound_handler': CodeGen.varNotFound_echo,
            # only called if defaultVarValue==None and the $var can't be found
            
            'debug': False,
            'keepCodeGeneratorResults': False,

            'blockMarkerStart':['<!-- START BLOCK: ',' -->'],
            'blockMarkerEnd':['<!-- END BLOCK: ',' -->'],
            'includeBlockMarkers': False,


            'extDelimeters':{'includeDirective': [delims['includeDirective_gobbleWS'],
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

            
            'responseErrorHandler': ErrorHandlers.ResponseErrorHandler,
            
            'codeGenerator':{
                'displayLogicblockEndings':['end if','end for'],            
                'internalDelims': delims['xml'],
                'tagTokenSeparator': '__@__',
                'indentationStep': ' '*4, # 4 spaces - used in the generated code
                'initialIndentLevel': 2, 
                
                ## must loop over these processores to handle
                # nested #include, #macro and #block Directives
                'includeDirectiveLoop':[('rawDirectives',
                                       CodeGen.preProcessRawDirectives),
                                      ('comments',
                                       CodeGen.preProcessComments),
                                      ('setDirectives',
                                       CodeGen.preProcessSetDirectives),
                                      ('dataDirectives',
                                       CodeGen.preProcessDataDirectives),
                                      ('blockDirectives',
                                       CodeGen.preProcessBlockDirectives),
                                      ('macroDirectives',
                                       CodeGen.preProcessMacroDirectives),
                                      ('lazyMacroCalls',
                                       CodeGen.preProcessLazyMacroCalls),
                                      ('explicitMacroCalls',
                                       CodeGen.preProcessExplicitMacroCalls),
                                      ('comments',
                                       CodeGen.preProcessComments),
                                      ('rawDirectives',
                                       CodeGen.preProcessRawDirectives),
                                      ('setDirectives',
                                       CodeGen.preProcessSetDirectives),
                                      ],
                
                'preProcessors': [('slurpDirectives',
                                   CodeGen.preProcessSlurpDirective),
                                  ('includeDirectiveLoop',
                                   includeDirectiveLoop), # see above
                                  ('displayLogic$Escaping',
                                   CodeGen.preProcessDisplayLogic),
                                  ],
                     
                'postProcessors': [('rawDirectives',
                                    CodeGen.postProcessRawDirectives),
                                   ('rawIncludeDirectives',
                                    CodeGen.postProcessRawIncludeDirectives),
                                   ],
                     
                'coreTags':{'displayLogic':{'type': EXEC_TAG_TYPE,
                                          'processor': CodeGen.displayLogicTagProcessor,
                                          'delims': [delims['displayLogic_gobbleWS'],
                                                     delims['displayLogic'],
                                                     ],
                                          },
                          'placeholders':{'type': EVAL_TAG_TYPE,
                                          'processor': CodeGen.placeholderTagProcessor,
                                          'delims': [delims['${,}'],delims['$']],
                                          ##the braced version must go first
                                        },
                          'setDirective':{'type': EXEC_TAG_TYPE,
                                          'processor': CodeGen.setDirectiveTagProcessor,
                                          'delims': [delims['setDirective'],],
                                          },
                          'cacheStartTag':{'type': EVAL_TAG_TYPE,
                                           'processor': CodeGen.cacheDirectiveStartTagProcessor,
                                           'delims': [delims['cacheDirectiveStartTag'],],
                                           },
                          'cacheEndTag':{'type': EVAL_TAG_TYPE,
                                           'processor': CodeGen.cacheDirectiveEndTagProcessor,
                                           'delims': [delims['cacheDirectiveEndTag'],],
                                           },                            

                            },
                        
                'generatedCodeFilters':[('removeEmptyStrings',
                                         CodeGen.removeEmptyStrings),
                                        ('addPerResponseCode',
                                         CodeGen.addPerResponseCode),
                                        ],
                        
                'masterErrorHandler':ErrorHandlers.CodeGeneratorErrorHandler,
                
                'stages':{1:{'title':'pre-processing',
                             'description':stageDescriptions[1],
                             'errorHandler':ErrorHandlers.Stage1ErrorHandler,
                             },
                          2:{'title':'translate-to-internal-tags',
                             'description':stageDescriptions[2],
                             'errorHandler':ErrorHandlers.Stage2ErrorHandler,
                             },
                          3:{'title':'post-processing',
                             'description':stageDescriptions[3],
                             'errorHandler':ErrorHandlers.Stage3ErrorHandler,
                             },
                          4:{'title':'convert-tags-to-code',
                             'description':stageDescriptions[4],
                             'errorHandler':ErrorHandlers.Stage4ErrorHandler,
                             },
                          5:{'title':'wrap-code-in-function-definition',
                             'description':stageDescriptions[5],
                             'errorHandler':ErrorHandlers.Stage5ErrorHandler,
                             },
                          6:{'title':'filter-generated-code',
                             'description':stageDescriptions[6],
                             'errorHandler':ErrorHandlers.Stage6ErrorHandler,
                             },
                          7:{'title':'execute-generated-code',
                             'description':stageDescriptions[7],
                             'errorHandler':ErrorHandlers.Stage7ErrorHandler,
                             },
                          },
                },
            }
        
    def addToSearchList(self, object, restart=True):
        self._searchList.append(object)
        if restart:
            self.startServer()

    def startServer(self):
        """Process and parse the template, then compile it into a function definition
        that is bound to self.__str__() and self.respond()"""
        
        self._errorMsgStack = []
        generatedFunction = self._codeGenerator( self._rawTemplate )
        self.__str__ = self._bindFunctionAsMethod( generatedFunction )
        self.respond = self._bindFunctionAsMethod( generatedFunction )
        
        if not self._settings['keepCodeGeneratorResults']:
            self._codeGeneratorResults = {}
        

    def _codeGenerator(self, template):
        
        """parse the template definition, generate a python code string from it,
        then execute the code string to create a python function which can be
        bound as a method of the Template.  Returns a reference to the function.
        
        stage 1 - the raw template is filtered using the pre-processors
        specified in the TemplateServer settings
        
        stage 2 - convert the coreTags to internal tags.  Core tags are: $var,
        ${var}, #if .../#, #for .../#, #set, and the PSP tags <%...%>,
        <%=...%>. Each internal tag will contain a token prefix to identify what
        type of tag it was originally.  These tokens are used in stage 4 to
        determine how the tag should be processed.

        stage 3 - the template is filtered for the 2nd time using the
        post-processors specified in the TemplateServer settings

        stage 4 - the tags that have been translated to the internal format are
        converted into chunks of python code

        stage 5 - the chunks of python code from stage 4 are wrapped up in a
        code string of a function definition

        stage 6 - the generated code string is filtered using the filters
        defined in the TemplateServer settings

        stage 7 - the generated code string is executed to produce a python
        function, that will become a method of the TemplateServer

        These stages are contain in a try: ... except: ... block that will
        provide helpful information for debugging if an error is caught."""
        
        settings = self._settings
        generatorSettings = settings['codeGenerator']
        stageSettings = generatorSettings['stages']
        debug = settings['debug']
        results = self._codeGeneratorResults = {}
        state = self._codeGeneratorState = {}
        self._localVarsList = []        # used to track vars from #set and #for
        
        try:
            ## stage 1 - preProcessing of the template string ##
            stage = 1
            if debug: results['stage1'] = []
            for preProcessor in generatorSettings['preProcessors']:
                template = preProcessor[1](self, template)
                if debug: results['stage1'].append((preProcessor[0], template))

                        
            ## stage 2 - translate the coreTag delimeters to internalDelims ##
            #  with tokens that will be recognized by the self._tagTokenProcessor
            stage = 2
            if debug: results['stage2'] = []
            template = template.replace("'''",r"\'\'\'") # ''' must be escaped
            for token, tagSettings in generatorSettings['coreTags'].items():
                for delimStruct in tagSettings['delims']:
                    # this loop allows multiple delims to be used for each token
                    template = CodeGen.swapDelims(
                        template, delimStruct,
                        generatorSettings['internalDelims']['start'] + token  \
                        + generatorSettings['tagTokenSeparator'],
                        generatorSettings['internalDelims']['end'],
                        )
                    if debug: results['stage2'].append( (token, template) )

                    
            ## stage 3 - postProcessing after the coreTag delim translation ##
            stage = 3
            if debug: results['stage3'] = []
            for postProcessor in generatorSettings['postProcessors']:
                template = postProcessor[1](self, template)
                if debug: results['stage3'].append( (postProcessor[0], template) )

    
            ## stage 4 - generate the python code for each of the tokenized tags ##
            #  a) separate internal tags from text in the template to create
            #     textVsTagsList 
            #  b) send textVsTagsList through self._tagTokenProcessor to generate
            #     the code pieces
            #  c) merge the code pieces into a single string
            stage = 4
            if debug: results['stage4'] = []
            
            # a)
            subStage = 'a'
            textVsTagsList = CodeGen.separateTagsFromText(
                template, generatorSettings['internalDelims']['placeholderRE'])
            if debug:
                results['stage4'].append(('textVsTagsList', textVsTagsList))
            # b)
            subStage = 'b'
            codePiecesFromTextVsTagsList = CodeGen.processTextVsTagsList(
                textVsTagsList,
                self._tagTokenProcessor)
            # c)
            subStage = 'c'
            codeFromTextVsTagsList = "".join(codePiecesFromTextVsTagsList)
            if debug:
                results['stage4'].append(('codeFromTextVsTagsList',
                                          codeFromTextVsTagsList))

            ## stage 5 - wrap the code up in a function definition ##
            stage = 5
            if debug: results['stage5'] = []
            indent = generatorSettings['indentationStep']
            generatedCode = \
                          "def generatedFunction(self, trans=None, iAmNested=False):\n" \
                          + indent * 1 + "try:\n" \
                          + indent * 2 + "#setupCodeInsertMarker\n" \
                          + indent * 2 + "outputList = []\n" \
                          + indent * 2 + "outputList += ['''" + codeFromTextVsTagsList + \
                          "''',]\n" \
                          + indent * 2 + "output = ''.join(outputList)\n" \
                          + indent * 2 + "if trans and not iAmNested:\n" \
                          + indent * 3 + "trans.response().write(output)\n" \
                          + indent * 2 + "return output\n" \
                          + indent * 1 + "except:\n" \
                          + indent * 2 + "print self._settings['responseErrorHandler']()\n" \
                          + indent * 2 + "raise\n" \
            
            if debug: results['stage5'].append( ('generatedCode', generatedCode) )

            
            ## stage 6 - final filtering of the generatedCode  ##
            stage = 6
            if debug: results['stage6'] = []
            for filter in generatorSettings['generatedCodeFilters']:
                generatedCode = filter[1](self, generatedCode)
                if debug: results['stage6'].append( (filter[0], generatedCode) )

            ## stage 7 - create "generatedFunction" in this namespace ##
            stage = 7
            if debug: results['stage7'] = []
            exec generatedCode
            if debug:
                results['stage7'].append(('generatedFunction', generatedFunction))
            
            ##
            self._generatedCode = generatedCode
            
            return generatedFunction
                
        except:
            ## call masterErrorHandler, which in turn calls the ErrorHandler ##
            # for the stage in which the error occurred
            print generatorSettings['masterErrorHandler']()
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

    def _tagTokenProcessor(self, tag, wrapOutput=True):
        """an abstract tag processor that will identify the tag type from its
        tagToken prefix and call the appropriate processor for that type of
        tag"""
        settings = self._settings

        tagToken, tag = tag.split(settings['codeGenerator']['tagTokenSeparator'])

        for token, tagSettings in settings['codeGenerator']['coreTags'].items():
            if tagToken == token:
                processedTag = tagSettings['processor'](self, tag)

                if not wrapOutput:
                    return processedTag
                elif tagSettings['type'] == EVAL_TAG_TYPE:
                    return "''', " + processedTag + ", '''"
                elif tagSettings['type'] == EXEC_TAG_TYPE:
                    return "''',]\n" + processedTag + "outputList += ['''"


    ## methods for dealing with the embedded NameMapper object references ##

    def mapName(self, name, default=None, executeCallables=False):
        """Returns a mapping for the placeholder name to its actual value

        This function is similar, but not identical, to Webware's valueForName!
        """

        for namespace in self._searchList:
            binding = valueForName(namespace, name, '<!NotFound!>')
            if binding != '<!NotFound!>':
                break

        if binding == '<!NotFound!>':
            if default!=None:
                binding = defaultVarValue
            elif self._settings['defaultVarValue']!=None:
                binding = self._settings['defaultVarValue']
            else:
                raise NameMapper.NotFound(name)

        if executeCallables and callable(binding):
            binding = binding()
        return binding


    def _setTimedRefresh(self, placeholderName, cacheRefreshInterval):
        nextUpdateTime = currentTime() + cacheRefreshInterval * 60 
        self._timedRefreshList.append(
            [placeholderName, nextUpdateTime, cacheRefreshInterval])
        self._checkForCacheRefreshes = True

    def _timedRefresh(self, currTime):
        """refresh all the cached NameMapper vars that are scheduled for a
        refresh at this time, and reschedule them for their next update.

        the entries in the recache list are in the format [name, interval,
        nextRecacheTime] """
        
        def updateList(item, currTime=currTime):
            if item[1] < currTime:
                item[1] = currTime + (item[2]*60) # reschedule for next update
                return True
            else:
                return False
            
        for name in filter(updateList, self._timedRefreshList):
            if self._settings['debug']:
                print repr(self), 'refreshing {' + name[0] + '} at time:', \
                      currentTime()
                print
                
            ## send it back through the tag processor to recache the value
            CodeGen.placeholderTagProcessor(
                self, tag=name[0], cacheType=CodeGen.TIMED_REFRESH_CACHE,
                cacheRefreshInterval=float(name[1]))
            
            ## the placeholderTagProcessor will have added a new entry to the
            # list which we don't need so ...
            self._timedRefreshList.pop() 

        
    def defineTemplateBlock(self, blockName, blockContents):
        """  """
        if not hasattr(self, '_blocks'):
            self._blocks = {}
            
        self._blocks[blockName]= blockContents

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
