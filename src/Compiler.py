#!/usr/bin/env python
# $Id: Compiler.py,v 1.41 2002/07/31 19:15:24 tavis_rudd Exp $
"""Compiler classes for Cheetah:
ModuleCompiler aka 'Compiler'
ClassCompiler
MethodCompiler

If you are trying to grok this code start with ModuleCompiler.__init__,
ModuleCompiler.compile, and ModuleCompiler.__getattr__.


Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
Version: $Revision: 1.41 $
Start Date: 2001/09/19
Last Revision Date: $Date: 2002/07/31 19:15:24 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__revision__ = "$Revision: 1.41 $"[11:-2]

##################################################
## DEPENDENCIES


import sys
import os
import os.path
from os.path import getmtime, exists
import re
import types
import time
import random

# intra-package imports ...
from _properties import Version
from SettingsManager import SettingsManager
from Parser import Parser, ParseError, specialVarRE, STATIC_CACHE, REFRESH_CACHE
from Utils.Indenter import indentize

##################################################
## CONSTANTS & GLOBALS 

try:
    True, False
except NameError:
    True, False = (1==1), (1==0)

##################################################
## CLASSES 

class Error(Exception):
    pass


class GenUtils:

    """An abstract baseclass for the Compiler classes that provides methods that
    perform generic utility functions or generate pieces of output code from
    information passed in by the Parser baseclass.  These methods don't do any
    parsing themselves."""


    def genTimeInterval(self, timeString):
        ##@@ TR: need to add some error handling here
        if timeString[-1] == 's':
            interval = float(timeString[:-1])
        elif timeString[-1] == 'm':
            interval = float(timeString[:-1])*60
        elif timeString[-1] == 'h':
            interval = float(timeString[:-1])*60*60
        elif timeString[-1] == 'd':
            interval = float(timeString[:-1])*60*60*24
        elif timeString[-1] == 'w':
            interval = float(timeString[:-1])*60*60*24*7
        else:                       # default to minutes
            interval = float(timeString)*60

        return interval
        
    def genCacheInfo(self, cacheToken):
        
        """Decipher a placeholder cachetoken
        """
        
        match = self.cacheTokenRE.match(cacheToken)
        subGrpDict = match.groupdict()
        cacheInfo = {}
        if subGrpDict['REFRESH_CACHE']:
            cacheInfo['type'] = REFRESH_CACHE
            cacheInfo['interval'] = self.genTimeInterval(subGrpDict['interval'])
        elif subGrpDict['STATIC_CACHE']:
            cacheInfo['type'] = STATIC_CACHE
        return cacheInfo                # is empty if no cache

    def genCacheInfoFromArgList(self, argList):
        cacheInfo = {'type':REFRESH_CACHE}
        for key, val in argList:
            if val[0] in '"\'':
                val = val[1:-1]

            if key == 'timer':
                key = 'interval'
                val = self.genTimeInterval(val)
                
            cacheInfo[key] = val
        return cacheInfo
        
        
    def genCheetahVar(self, nameChunks, plain=False):
        if self.setting('useNameMapper') and not plain:
            return self.genNameMapperVar(nameChunks)
        else:
            return self.genPlainVar(nameChunks)
    
    def genNameMapperVar(self, nameChunks):
        
        """Generate valid Python code for a Cheetah $var, using NameMapper
        (Unified Dotted Notation with the SearchList).

        nameChunks = list of var subcomponents represented as tuples
          [ (namemapperPart,autoCall,restOfName),
          ]
        where:
          namemapperPart = the dottedName base
          autocall = where NameMapper should use autocalling on namemapperPart
          restOfName = any arglist, index, or slice

        If restOfName contains a call arglist (e.g. '(1234)') then autocall is
        False, otherwise it defaults to True. It is overridden by the global
        setting 'useAutocalling' if this setting is False.

        EXAMPLE
        ------------------------------------------------------------------------
        if the raw Cheetah Var is
          $a.b.c[1].d().x.y.z
          
        nameChunks is the list
          [ ('a.b.c',1,'[1]'), # A
            ('d',0,'()'),      # B
            ('x.y.z',1,''),    # C
          ]
        
        When this method is fed the list above it returns
          VFN(VFN(VFS(SL, 'a.b.c',1)[1], 'd',0)(), 'x.y.z',1)
        which can be represented as
          VFN(B`, C[0], str(ACS and C[1]))C[2]
        where:
          ACS = self.setting('useAutocalling') = 1 in this example
          VFN = NameMapper.valueForName
          VFS = NameMapper.valueFromSearchList
          SL = self.searchList()

          A = ('a.b.c',1,'[1]')
          B = ('d',0,'()')
          C = ('x.y.z',1,'')

          B` = VFN(A`, B[0], str(ACS and B[1]))B[2]
          A` = VFS(SL, A[0], str(ACS and A[1]))A[2]
          
        """

        autoCall = self.setting('useAutocalling')
        nameChunks.reverse()

        chunk = nameChunks.pop()
        firstBit = chunk[0].split('.')[0]

        if chunk[0] in self.localVars() or chunk[0] in self.globalVars():
            # @@TR: note this method won't use autocalling on these vars!!            
            translatedName = chunk[0] + chunk[2]
        elif firstBit in self.localVars() or firstBit in self.globalVars():
            translatedName = ('VFN(' + firstBit +
                              ',"' + '.'.join(chunk[0].split('.')[1:]) +
                              '",' + str(autoCall and chunk[1]) + ')'
                              + chunk[2])            
        else:
            translatedName = ('VFS(SL,"' + chunk[0] +
                              '",' + str(autoCall and chunk[1]) + ')'
                              + chunk[2])
        
        while nameChunks:
            chunk = nameChunks.pop()
            translatedName = ('VFN(' + translatedName +
                              ',"' + chunk[0] +
                              '",' + str(autoCall and chunk[1]) + ')'
                              + chunk[2])

        return translatedName

    def genPlainVar(self, nameChunks):
        
        """Generate Python code for a Cheetah $var without using NameMapper
        (Unified Dotted Notation with the SearchList)."""
        
        nameChunks.reverse()
        chunk = nameChunks.pop()
        translatedName = chunk[0] + chunk[2]
        
        while nameChunks:
            chunk = nameChunks.pop()
            translatedName = (translatedName + '.' + chunk[0] + chunk[2])
                    
        return translatedName
    
    ## utility methods 

    def unescapeCheetahVars(self, theString):
        """Unescape any escaped Cheetah \$vars in the string."""
        
        token = self.setting('cheetahVarStartToken')
        return theString.replace('\\' + token, token)

    def unescapeDirectives(self, theString):
        """Unescape any escaped Cheetah \$vars in the string."""
        
        token = self.setting('directiveStartToken')
        return theString.replace('\\' + token, token)

##################################################
## METHOD COMPILERS

class MethodCompiler(SettingsManager, GenUtils):
    def __init__(self, methodName, classCompiler, settings={}):
        SettingsManager.__init__(self)
        self._settings = settings
        self._methodName = methodName

    def setupState(self):
        self._indent = self.setting('indentationStep')
        self._indentLev = self.setting('initialMethIndentLevel')
        self._pendingStrConstChunks = []
        self._localVars = ['self']
        if self.setting('recognize__builtins__'):
            import __builtin__
            self._localVars.extend( dir(__builtin__) )

        self._methodSignature = None
        self._methodDef = None
        self._docStringLines = []
        self._methodBodyChunks = []

        self._cacheRegionOpen = False
        
    def cleanupState(self):
        pass

    def methodName(self):
        return self._methodName

    def setMethodName(self, name):
        self._methodName = name

    def localVars(self):
        return self._localVars
        
    ## methods for managing indentation
    
    def indentation(self):
        return self._indent * self._indentLev
    
    def indent(self):
        self._indentLev +=1
        
    def dedent(self):
        if self._indentLev:
            self._indentLev -=1
        else:
            raise Error('Attempt to dedent when the indentLev is 0')

    ## methods for final code wrapping

    def methodDef(self):
        if self._methodDef:
            return self._methodDef
        else:
            return self.wrapCode()

    __str__ = methodDef
    
    def wrapCode(self):
        self.commitStrConst()
        methodDefChunks = (
            self.methodSignature(),
            '\n',
            self.docString(),
            self.methodBody(),
            )
        methodDef = ''.join(methodDefChunks)
        self._methodDef = methodDef
        return methodDef

    def methodSignature(self):
        return self._indent + self._methodSignature + ':'

    def setMethodSignature(self, signature):
        self._methodSignature = signature

    def methodBody(self):
        return ''.join( self._methodBodyChunks )

    def docString(self):
        ind = self._indent*2
        
        docStr = (ind + '"""\n' + ind +
                  ('\n' + ind).join(self._docStringLines) +
                  '\n' + ind + '"""\n')
        return  docStr

    ## methods for adding code

    def addRawChunk(self, chunk):
        self._methodBodyChunks.append(chunk)

    def addMethDocString(self, line):
        self._docStringLines.append(line)

    def addLocalVars(self, varnameList):
        self._localVars.extend(varnameList)
        
    def addChunk(self, chunk):
        self.commitStrConst()
        chunk = "\n" + self.indentation() + chunk
        self.addRawChunk(chunk)

    def appendToPrevChunk(self, appendage):
        self._methodBodyChunks[-1] = self._methodBodyChunks[-1] + appendage

    def addWriteChunk(self, chunk):
        self.addChunk('write(' + chunk + ')')

    def addFilteredChunk(self, chunk):
        self.addWriteChunk('filter(' + chunk + ')')

    def addStrConst(self, strConst):
        self.appendToPrevStrConst(strConst)

    def appendToPrevStrConst(self, strConst):
        if self._pendingStrConstChunks:
            self._pendingStrConstChunks.append(strConst)
        else:
            self._pendingStrConstChunks = [strConst]
        
    def commitStrConst(self):
        if self._pendingStrConstChunks:
            strConst = self.unescapeCheetahVars(''.join(self._pendingStrConstChunks))
            strConst = self.unescapeDirectives(strConst)
            self._pendingStrConstChunks = []
            if self.setting('reprShortStrConstants') and \
               strConst.count('\n') < self.setting('reprNewlineThreshold'):
                self.addWriteChunk( repr(strConst).replace('\\012','\\n'))
            else:
                self.addWriteChunk(
                    "'''" + strConst.replace('\\','\\\\').replace("'''","'\'\'\'")
                    + "'''" )

    def delLeadingWS(self):
        if self._pendingStrConstChunks:
            src = self._pendingStrConstChunks[-1]
            BOL = max(src.rfind('\n')+1, src.rfind('\r')+1, 0)
            if BOL < len(src):
                self._pendingStrConstChunks[-1] = src[:BOL]
        
    def addMethComment(self, comm):
        offSet = self.setting('commentOffset')
        self.addChunk('#' + ' '*offSet + comm)


    def addSilent(self, expr):
        self.addChunk( expr )
        
    def addSet(self, LVALUE, OP, RVALUE, isGlobal=True):
        ## we need to split the LVALUE to deal with globalSetVars
        #  and keeping track of localVars for this method
        splitPos1 = LVALUE.find('.')
        splitPos2 = LVALUE.find('[')
        if splitPos1 > 0 and splitPos2==-1:
            splitPos = splitPos1
        elif splitPos1 > 0 and splitPos1 < max(splitPos2,0):
            splitPos = splitPos1
        else:
            splitPos = splitPos2
            
        if splitPos >0:
            primary = LVALUE[:splitPos]
            secondary = LVALUE[splitPos:]
        else:
            primary = LVALUE
            secondary = ''

        if isGlobal:
            LVALUE = 'globalSetVars["' + primary + '"]' + secondary            
        else:
            if primary not in self._localVars:
                self.addLocalVars( (primary,) )
            
        self.addChunk( LVALUE + ' ' + OP + ' ' + RVALUE.strip() )

    def addWhile(self, expr):
        self.addIndentingDirective(expr)
        
    def addFor(self, expr):
        self.addIndentingDirective(expr)

    def addIndentingDirective(self, expr):
        if expr and not expr[-1] == ':':
            expr = expr  + ':'
        self.addChunk( expr )
        self.indent()

    def addReIndentingDirective(self, expr):
        self.commitStrConst()
        self.dedent()
        if not expr[-1] == ':':
            expr = expr  + ':'
            
        self.addChunk( expr )
        self.indent()

    def addIf(self, expr):
        self.addIndentingDirective(expr)

    def addElse(self, expr):
        expr = re.sub(r'else[ \f\t]+if','elif', expr)
        self.addReIndentingDirective(expr)

    def addTry(self, expr):
        self.addIndentingDirective(expr)
        
    def addExcept(self, expr):
        self.addReIndentingDirective(expr)
        
    def addFinally(self, expr):
        self.addReIndentingDirective(expr)
            
    def addReturn(self, expr):
        self.addChunk(expr)

    def addPSP(self, PSP):
        self.commitStrConst()
        autoIndent = False
        if PSP[0] == '=':
            PSP = PSP[1:]
            if PSP:
                self.addWriteChunk('filter(' + PSP + ')')
            return
                    
        elif PSP.lower() == 'end':
            self.dedent()
            return
        elif PSP[-1] == '$':
            autoIndent = True
            PSP = PSP[:-1]
        elif PSP[-1] == ':':
            autoIndent = True
            
        for line in PSP.splitlines():
            self.addChunk(line)
            
        if autoIndent:
            self.indent()

    
    def cacheID(self):
        return self._cacheID

    def nextCacheID(self):
        self._cacheID = str(random.randrange(100, 999)) \
                        + str(random.randrange(10000, 99999))
        return self._cacheID

    def startCacheRegion(self, cacheInfo, lineCol):
        ID = self.nextCacheID()
        interval = cacheInfo.get('interval',None)
        test = cacheInfo.get('test',None)
        self._cacheRegionOpen = True    # attrib of current methodCompiler
        
        self.addChunk('## START CACHE REGION: at line, col ' + str(lineCol) + ' in the source.')
        self.addChunk('RECACHE = True')
        
        self.addChunk('if not self._cacheData.has_key(' + repr(ID) + '):')
        self.indent()
        if cacheInfo.has_key('id'):
            self.addChunk("self._cacheIndex['" +
                          cacheInfo['id'] +
                          "'] = '" + ID +"'")
        if not (interval or test):
            self.addChunk('pass')
        if interval:
            setRefreshTime = ('self.__cache' + ID +
                              '__refreshTime = currentTime() + ' + str(interval))
            self.addChunk(setRefreshTime)
            self.dedent()
            self.addChunk('elif currentTime() > self.__cache' + ID
                               + '__refreshTime:')
            self.indent()
            self.addChunk(setRefreshTime)
            self.addMethDocString('This cache will be refreshed every ' +
                                       str(interval) + ' seconds.')
        if test:
            self.dedent()
            self.addChunk('elif ' + test + ':')
            self.indent()
            self.addChunk('RECACHE = True')
            
        self.dedent()
        self.addChunk('else:')
        self.indent()
        self.addChunk('RECACHE = False')
        self.dedent()
        self.addChunk('if RECACHE:')
        self.indent()
        self.addChunk('orig_trans = trans')
        self.addChunk('trans = cacheCollector = DummyTransaction()')
        self.addChunk('write = cacheCollector.response().write')
        
    def endCacheRegion(self):
        self._cacheRegionOpen = False
        self.addChunk('trans = orig_trans')
        self.addChunk('write = trans.response().write')
        self.addChunk('self._cacheData[' + repr(self.cacheID())
                      + '] = cacheCollector.response().getvalue()')
        self.addChunk('del cacheCollector')
        self.dedent()
        self.addWriteChunk( 'self._cacheData[' + repr(self.cacheID()) + ']' )
        self.addChunk('## END CACHE REGION')
        self.addChunk('')

class AutoMethodCompiler(MethodCompiler):

    def setupState(self):
        MethodCompiler.setupState(self)
        self._localVars.extend(['trans',
                                'dummyTrans',
                                'VFS',
                                'VFN',
                                'SL',
                                'globalSetVars',
                                'write',
                                'filter',
                                'currentTime',
                                ])
        self._argStringList = [ ("self",None) ]
        self._streamingEnabled = True
        
    def cleanupState(self):
        MethodCompiler.cleanupState(self)
        self.commitStrConst()
        if self._cacheRegionOpen:
            self.endCacheRegion()

            
        self._indentLev = self.setting('initialMethIndentLevel')
        mainBodyChunks = self._methodBodyChunks
        self._methodBodyChunks = []
        self.addAutoSetupCode()
        self._methodBodyChunks.extend(mainBodyChunks)
        self.addAutoCleanupCode()
        if self._streamingEnabled:
            for argName, defVal in  [ ('trans', 'None'),
                                      ("dummyTrans","False"),
                                      ("VFS","valueFromSearchList"), 
                                      ("VFN","valueForName"),
                                      ("getmtime","getmtime"),
                                      ("currentTime","time.time"),
                                      ]:
                self.addMethArg(argName, defVal)
        
    def addAutoSetupCode(self):
        if self._streamingEnabled:
            self.addChunk('if not trans:')
            self.indent()
            self.addChunk('trans = DummyTransaction()')
            self.addChunk('dummyTrans = True')
            self.dedent()
        else:
            self.addChunk('trans = DummyTransaction()')
            self.addChunk('dummyTrans = True')
        self.addChunk('write = trans.response().write')
        self.addChunk('SL = self._searchList')
        self.addChunk('filter = self._currentFilter')
        self.addChunk('globalSetVars = self._globalSetVars')
        self.addChunk('')

        self.addChunk("#" *40)
        self.addChunk('## START - generated method body')
        self.addChunk('')

    def addAutoCleanupCode(self):
        self.addChunk('')
        self.addChunk("#" *40)
        self.addChunk('## END - generated method body')
        self.addChunk('')
        self.addStop()
        self.addChunk('')
        
    def addStop(self, expr=None):
        self.addChunk('if dummyTrans:')
        self.indent()
        self.addChunk('return trans.response().getvalue()')
        self.dedent()
        self.addChunk('else:')
        self.indent()
        self.addChunk('return ""')
        self.dedent()

    def addMethArg(self, name, defVal=None):
        asteriskPos = max(name.rfind('*')+1, 0)
        if asteriskPos:
            self._streamingEnabled = False
        self._argStringList.append( (name,defVal) )
        self.addLocalVars((name[asteriskPos:],))
        
    def methodSignature(self):
        argStringChunks = []
        for arg in self._argStringList:
            chunk = arg[0]
            if not arg[1] == None:
                chunk += '=' + arg[1]
            argStringChunks.append(chunk)
        return (self._indent + "def " + self.methodName() + "(" +
                (',\n' + self._indent*3).join(argStringChunks) + "):\n\n")


##################################################
## CLASS COMPILERS

class ClassCompiler(SettingsManager, GenUtils):
    
    _activeMethods = None      # converted to a list at runtime
    
    def __init__(self, className, mainMethodName='respond',
                 templateObj=None,
                 fileName=None,
                 settings={}):

        SettingsManager.__init__(self)
        self._settings = settings
        self._fileName = fileName
        self._className = className
        self._mainMethodName = mainMethodName
        self._templateObj = templateObj
        self.setupState()
        methodCompiler = self.spawnMethodCompiler(mainMethodName)
        methodCompiler.addMethDocString('This is the main method generated by Cheetah')
        self.setActiveMethodCompiler(methodCompiler)
        
        if fileName and self.setting('monitorSrcFile'):

            self.addChunkToInit('self._filePath = ' + repr(fileName))
            self.addChunkToInit('self._fileMtime = ' + str(getmtime(fileName)) )
            if self._templateObj:
                setattr(self._templateObj, '_filePath', fileName)
                setattr(self._templateObj, '_fileMtime', getmtime(fileName))
                
            self.addChunk('if exists(self._filePath) and ' +
                          'getmtime(self._filePath) > self._fileMtime:')
            self.indent()
            self.addChunk('self.compile(file=self._filePath)')
            self.addChunk(
                'write(getattr(self, self._mainCheetahMethod_for_' + self._className +
                ')(trans=trans))')            
            self.addStop()
            self.dedent()

    def __getattr__(self, name):

        """Provide access to the methods and attributes of the MethodCompiler
        at the top of the activeMethods stack: one-way namespace sharing

        
        WARNING: Use .setMethods to assign the attributes of the MethodCompiler
        from the methods of this class!!! or you will be assigning to attributes
        of this object instead."""
        

        if self.__dict__.has_key(name):
            return self.__dict__[name]
        elif self.__class__.__dict__.has_key(name):
            return self.__class__.__dict__[name]
        elif self._activeMethods and hasattr(self._activeMethods[-1], name):
            return getattr(self._activeMethods[-1], name)
        else:
            raise AttributeError, name

    def setupState(self):
        self._classDef = None
        self._activeMethods = []        # stack while parsing/generating
        self._finishedMethods = []      # store by order
        self._methodsIndex = {}      # store by name
        self._baseClass = 'Template'
        self._classDocStringLines = []
        self._generatedAttribs = []      # printed after methods in the gen class def
        self._initMethChunks = []
        self._alias__str__ = True      # should we set the __str__ alias
        
        self._blockMetaData = {}
        self._errorCatcherCount = 0
        self._placeholderToErrorCatcherMap = {}

    def setupInitMethod(self):
        __init__ = self.spawnMethodCompiler('__init__', klass=MethodCompiler)
        __init__.setupState()
        __init__.setMethodSignature("def __init__(self, *args, **KWs)")
        __init__.addChunk("%s.__init__(self, *args, **KWs)" % self._baseClass)
        for chunk in self._initMethChunks:
            __init__.addChunk(chunk)
        __init__.cleanupState()
        self.swallowMethodCompiler(__init__, pos=0)

    def cleanupState(self):
        while self._activeMethods:
            methCompiler = self.getActiveMethodCompiler()
            self.swallowMethodCompiler(methCompiler)
        self.setupInitMethod()
        if self._mainMethodName == 'respond':
            self._generatedAttribs.append('__str__ = respond')
            if self._templateObj:
                self._templateObj.__str__ = self._templateObj.respond
        self.addAttribute('_mainCheetahMethod_for_' + self._className +
                           '= ' + repr(self._mainMethodName)
                           )

    
    def setClassName(self, name):
        self._className = name

    def className(self):
        return self._className
       
    def setBaseClass(self, baseClass):
        self._baseClass = baseClass
        
    def setMainMethodName(self, methodName):
        ## change the name in the methodCompiler and add new reference
        mainMethod = self._methodsIndex[self._mainMethodName]
        mainMethod.setMethodName(methodName)
        self._methodsIndex[methodName] = mainMethod

        ## make sure that fileUpdate code still works properly:
        chunkToChange = ('write(self.' + self._mainMethodName + '(trans=trans))')
        chunks = mainMethod._methodBodyChunks
        if chunkToChange in chunks:
            for i in range(len(chunks)):
                if chunks[i] == chunkToChange:
                    chunks[i] = ('write(self.' + methodName + '(trans=trans))')


        ## get rid of the old reference and update self._mainMethodName
        del self._methodsIndex[self._mainMethodName]
        self._mainMethodName = methodName
        
    
    def spawnMethodCompiler(self, methodName, klass=AutoMethodCompiler):
        methodCompiler = klass(methodName,
                               classCompiler=self,
                               settings=self.settings(),
                               )
        self._methodsIndex[methodName] = methodCompiler
        methodCompiler.setupState()
        return methodCompiler

    def setActiveMethodCompiler(self, methodCompiler):
        self._activeMethods.append(methodCompiler)

    def getActiveMethodCompiler(self):
        return self._activeMethods.pop()
        
    def swallowMethodCompiler(self, methodCompiler, pos=None):
        methodCompiler.cleanupState()
        if pos==None:
            self._finishedMethods.append( methodCompiler )
        else:
            self._finishedMethods.insert(pos, methodCompiler)

        if self._templateObj and methodCompiler.methodName() != '__init__':
            self._templateObj._bindCompiledMethod(methodCompiler)
        return methodCompiler
        
    def finishedMethods(self):
        return self._finishedMethods

    def addClassDocString(self, line):
        self._classDocStringLines.append(line)

    def addChunkToInit(self,chunk):
        self._initMethChunks.append(chunk)

    def addAttribute(self, attribExpr):
        ## first test to make sure that the user hasn't used any fancy Cheetah syntax
        #  (placeholders, directives, etc.) inside the expression 
        if attribExpr.find('VFN(') != -1 or attribExpr.find('VFS(SL,') != -1:
            raise ParseError(self,
                             'Invalid #attr directive.' +
                             ' It should only contain simple Python literals.')
        ## now add the attribute
        self._generatedAttribs.append(attribExpr)
        if self._templateObj:
            exec('self._templateObj.' + attribExpr.strip())

    def addSettingsToInit(self, settingsStr, settingsType='ini'):
        if settingsType=='python':
            reader = 'updateSettingsFromPySrcStr'
        else:            
            reader = 'updateSettingsFromConfigStr'

        settingsCode = ("self." + reader + "('''" +
                        settingsStr.replace("'''","\'\'\'") +
                        "''')")
        self.addChunkToInit(settingsCode)

    def addErrorCatcher(self, codeChunk, rawCode='', lineCol=''):
        if self._placeholderToErrorCatcherMap.has_key(rawCode):
            methodName = self._placeholderToErrorCatcherMap[rawCode]
            if not self.setting('outputRowColComments'):
                self._methodsIndex[methodName].addMethDocString(
                    'plus at line, col ' + str(lineCol))
            return methodName

        self._errorCatcherCount += 1
        methodName = '__errorCatcher' + str(self._errorCatcherCount)
        self._placeholderToErrorCatcherMap[rawCode] = methodName
        
        catcherMeth = self.spawnMethodCompiler(methodName, klass=MethodCompiler)
        catcherMeth.setupState()
        catcherMeth.setMethodSignature('def ' + methodName +
                                     '(self, localsDict={})')
        catcherMeth.addMethDocString('Generated from ' + rawCode +
                                   ' at line, col ' + str(lineCol) + '.') 
        catcherMeth.addChunk('try:')
        catcherMeth.indent()
        catcherMeth.addChunk("return eval('''" + codeChunk +
                             "''', globals(), localsDict)")
        catcherMeth.dedent()
        catcherMeth.addChunk('except self._errorCatcher.exceptions(), e:')
        catcherMeth.indent()        
        catcherMeth.addChunk("return self._errorCatcher.warn(exc_val=e, code= " +
                             repr(codeChunk) + " , rawCode= " +
                             repr(rawCode) + " , lineCol=" + str(lineCol) +")")
        
        catcherMeth.cleanupState()
        
        self.swallowMethodCompiler(catcherMeth)
        return methodName

    ## code wrapping methods
    
    def classDef(self):
        if self._classDef:
            return self._classDef
        else:
            return self.wrapClassDef()

    __str__ = classDef
    
    def wrapClassDef(self):
        self.addClassDocString('')
        self.addClassDocString(self.setting('defDocStrMsg'))
        ind = self.setting('indentationStep')
        classDefChunks = (
            self.classSignature(),
            self.classDocstring(),
            ind + '#'*50,
            ind + '## GENERATED METHODS',
            '\n',
            self.methodDefs(),
            ind + '#'*50,
            ind + '## GENERATED ATTRIBUTES',
            '\n',
            self.attributes(),
            )

        classDef = '\n'.join(classDefChunks)
        self._classDef = classDef
        return classDef


    def classSignature(self):
        return "class %s(%s):" % (self.className(), self._baseClass)
        
    def classDocstring(self):
        ind = self.setting('indentationStep')
        docStr = ('%(ind)s"""\n%(ind)s' +
                  '\n%(ind)s'.join(self._classDocStringLines) +
                  '\n%(ind)s"""\n'
                  ) % {'ind':ind}
        return  docStr

    def methodDefs(self):
        methodDefs = [str(methGen) for methGen in self.finishedMethods() ]
        return '\n\n'.join(methodDefs)

    def attributes(self):
        attribs = [self.setting('indentationStep') + str(attrib)
                      for attrib in self._generatedAttribs ]
        return '\n\n'.join(attribs)


    
class AutoClassCompiler(ClassCompiler):
    pass


##################################################
## MODULE COMPILERS
        
class ModuleCompiler(Parser, GenUtils):
    
    _activeClasses = None               # converted to a list at runtime
    
    def __init__(self, source=None, file=None, moduleName='GenTemplate',
                 mainClassName=None,
                 mainMethodName='respond',
                 templateObj=None,
                 settings={}):
        
        self._templateObj = templateObj
        self._compiled = False
        self._moduleName = moduleName
        if not mainClassName:
            self._mainClassName = moduleName
        else:
            self._mainClassName = mainClassName
        self._mainMethodName = mainMethodName

        
        self._filePath = None
        self._fileMtime = None
        
        if source and file:
            raise TypeError("Cannot compile from a source string AND file.")
        elif type(file) == types.StringType: # it's a filename.
            f = open(file) # Raises IOError.
            source = f.read()
            f.close()
            self._filePath = file
            self._fileMtime = os.path.getmtime(file)
        elif hasattr(file, 'read'):
            source = file.read()  # Can't set filename or mtime--they're not accessible.
        elif file:
            raise TypeError("'file' argument must be a filename string or file-like object")


        if self._filePath:
            self._fileDirName, self._fileBaseName = os.path.split(self._filePath)
            self._fileBaseNameRoot, self._fileBaseNameExt = \
                                    os.path.splitext(self._fileBaseName)
            
        source = str( source )
        # by converting to string here we allow objects such as other Templates
        # to be passed in

        # Handle the #indent directive by converting it to other directives.
        # (Over the long term we'll make it a real directive.)
        if source.find('#indent') != -1:
            source = indentize(source)
        
        Parser.__init__(self, source, filename=self._filePath)
        self._initializeSettings()
        self.updateSettings(settings)
        self.configureParser()
        self.setupState()
        self.initDirectives()

    def __getattr__(self, name):

        """Provide access to the methods and attributes of the ClassCompiler:
        one-way namespace sharing

        WARNING: Use .setMethods to assign the attributes of the ClassCompiler
        from the methods of this class!!! or you will be assigning to attributes
        of this object instead."""
        
        if self.__dict__.has_key(name):
            return self.__dict__[name]
        elif self.__class__.__dict__.has_key(name):
            return self.__class__.__dict__[name]
        elif self._activeClasses and hasattr(self._activeClasses[-1], name):
            return getattr(self._activeClasses[-1], name)
        else:
            raise AttributeError, name


    def _initializeSettings(self):
        Parser._initializeSettings(self)
        defaults = {
            'indentationStep': ' '*4, 
            'initialMethIndentLevel': 2,

            'monitorSrcFile':False,
            
            ## controlling the handling of Cheetah $vars
            'useNameMapper': True,      # Unified dotted notation and the searchList
            'useAutocalling': True,
            'recognize__builtins__':True,
            'useErrorCatcher':False,

            ## controlling the aesthetic appearance of the generated code
            'commentOffset': 1,
            # should shorter str constant chunks be printed using repr rather than ''' quotes
            'reprShortStrConstants': True, 
            'reprNewlineThreshold':3,
            'outputRowColComments':True,

            ## should #block's be wrapped in a comment in the template's output
            'includeBlockMarkers': False,   
            'blockMarkerStart':('\n<!-- START BLOCK: ',' -->\n'),
            'blockMarkerEnd':('\n<!-- END BLOCK: ',' -->\n'),
            
            'defDocStrMsg':'Autogenerated by CHEETAH: The Python-Powered Template Engine'
            }
        self.updateSettings( defaults )

    def setupState(self):
        self._activeClasses = []
        self._finishedClasses = []      # listed by ordered 
        self._finishedClassIndex = {}  # listed by name
        
        self._moduleDef = None
        self._moduleShBang = '#!/usr/bin/env python'
        self._moduleHeaderLines = []
        self._moduleDocStringLines = []
        self._specialVars = {}

        self._importStatements = [
            "import sys",
            "import os",
            "import os.path",
            "from os.path import getmtime, exists",
            "import time",
            "import types",
            "from Cheetah.Template import Template",
            "from Cheetah.DummyTransaction import DummyTransaction",
            "from Cheetah.NameMapper import NotFound, valueForName, valueFromSearchList",
            "import Cheetah.Filters as Filters",
            "import Cheetah.ErrorCatchers as ErrorCatchers",
            ]        

        self._globalVars = ['sys',
                            'os',
                            'os.path',
                            'time',
                            'types',
                            'Template',
                            'DummyTransaction',
                            'NotFound',
                            'Filters',
                            'ErrorCatchers',
                            'True',
                            'False',
                            'None',
                            ]
        
        self._moduleConstants = [
            "try:",
            "    True, False",
            "except NameError:",
            "    True, False = (1==1), (1==0)",
            "VFS=valueFromSearchList",
            "VFN=valueForName",
            "currentTime=time.time",
            ]

        self._errorCatcherOn = False
        
    def compile(self):
        classCompiler = self.spawnClassCompiler(self._mainClassName)            
        self.addActiveClassCompiler(classCompiler)
        self.parse()
        self.swallowClassCompiler(self.getActiveClassCompiler())
        self._compiled = True

        
    def spawnClassCompiler(self, className, klass=AutoClassCompiler,
                           mainMethodName='respond'):
        classCompiler = klass(className,
                              mainMethodName=self._mainMethodName,
                              templateObj=self._templateObj,
                              fileName=self._filePath,
                              settings=self.settings(),
                              )
        return classCompiler

    def addActiveClassCompiler(self, classCompiler):
        self._activeClasses.append(classCompiler)

    def getActiveClassCompiler(self):
        return self._activeClasses.pop()
        
    def swallowClassCompiler(self, classCompiler):
        classCompiler.cleanupState()
        self._finishedClasses.append( classCompiler )
        self._finishedClassIndex[classCompiler.className()] = classCompiler
        return classCompiler

    def finishedClasses(self):
        return self._finishedClasses

    def globalVars(self):
        return self._globalVars
    
    def addGlobalVars(self, varNames):
        self._globalVars.extend(varNames)
        self._globalVars.sort()
        self._globalVars.reverse()


    def errorCatcherIsOn(self):
        return self._errorCatcherOn
    
    def turnErrorCatcherOn(self):
        self._errorCatcherOn = True

    def turnErrorCatcherOff(self):
        self._errorCatcherOn = False
        
    ## gen methods
        
    def closeDirective(self, lineClearToStartToken, endOfFirstLinePos):

        if self.matchDirectiveEndToken():
            self.getDirectiveEndToken()
        elif lineClearToStartToken and (not self.atEnd()) and self.peek() in '\r\n':
            self.readToEOL(gobble=True)
            
        if lineClearToStartToken and (self.atEnd() or self.pos() > endOfFirstLinePos):
            self.delLeadingWS()
    
    ## methods for adding stuff to the module and class definitions
    
    def addShBang(self, shBang):
        self._moduleShBang = shBang
    
    def addModuleHeader(self, line):
        self._moduleHeaderLines.append(line)
        
    def addModuleDocString(self, line):        
        self._moduleDocStringLines.append(line)

    def addSpecialVar(self, basename, contents):
        self._specialVars['__' + basename + '__'] = contents.strip()

    def addImportStatement(self, importStatement):
        self._importStatements.append(importStatement)

    def addGlobalCodeChunk(self, codeChunk):
        self._globalCodeChunks.append(codeChunk)

    def addComment(self, comm):
        if re.match(r'#+$',comm):      # skip bar comments
            return
        
        specialVarMatch = specialVarRE.match(comm)
        if specialVarMatch:
            return self.addSpecialVar(specialVarMatch.group(1),
                                      comm[specialVarMatch.end():])
        elif comm.startswith('doc:'):
            addLine = self.addMethDocString
            comm = comm[len('doc:'):].strip()
        elif comm.startswith('doc-method:'):
            addLine = self.addMethDocString
            comm = comm[len('doc-method:'):].strip()
        elif comm.startswith('doc-module:'):
            addLine = self.addModuleDocString
            comm = comm[len('doc-module:'):].strip()
        elif comm.startswith('doc-class:'):
            addLine = self.addClassDocString
            comm = comm[len('doc-class:'):].strip()
        elif comm.startswith('header:'):
            addLine = self.addModuleHeader
            comm = comm[len('header:'):].strip()
        else:
            addLine = self.addMethComment

        for line in comm.splitlines():
            addLine(line)

    ## methods for module code wrapping
    
    def moduleDef(self):
        if not self._compiled:
            self.compile()
        if self._moduleDef:
            return self._moduleDef
        else:
            return self.wrapModuleDef()
        
    __str__ = moduleDef


    def wrapModuleDef(self):
        self.addModuleDocString('')
        self.addModuleDocString(self.setting('defDocStrMsg'))
        self.addModuleDocString(' CHEETAH VERSION: ' + Version)
        self.addSpecialVar('CHEETAH_version', Version)
        self.addModuleDocString(' Generation time: ' + self.timestamp())
        self.addSpecialVar('CHEETAH_genTime', self.timestamp())
        if self._filePath:
            self.addSpecialVar('CHEETAH_src', self._filePath)
            self.addModuleDocString('   Source file: ' + self._filePath)
            self.addModuleDocString('   Source file last modified: ' +
                                    self.timestamp(self._fileMtime))
            
        moduleDef = """%(header)s
%(docstring)s
%(specialVars)s

##################################################
## DEPENDENCIES

%(imports)s

##################################################
## MODULE CONSTANTS

%(constants)s

##################################################
## CLASSES

%(classes)s

%(footer)s
""" %   {'header':self.moduleHeader(),
         'docstring':self.moduleDocstring(),
         'specialVars':self.specialVars(),
         'imports':self.importStatements(),
         'constants':self.moduleConstants(),
         'classes':self.classDefs(),
         'footer':self.moduleFooter(),
         }
       
        self._moduleDef = moduleDef
        return moduleDef

    def timestamp(self, theTime=None):
        if not theTime:
            theTime = time.time()
        return time.asctime(time.localtime(theTime))
    
    def moduleHeader(self):
        header = self._moduleShBang + '\n'
        if self._moduleHeaderLines:
            offSet = self.setting('commentOffset')
        
            header += (
                '#' + ' '*offSet + 
                ('\n#'+ ' '*offSet).join(self._moduleHeaderLines) +
                '\n'
                )

        return header

    def moduleDocstring(self):
        docStr = ('"""' +
                  '\n'.join(self._moduleDocStringLines) +
                  '\n"""\n'
                  )
        return  docStr


    def specialVars(self):
        chunks = []
        theVars = self._specialVars
        keys = theVars.keys()
        keys.sort()
        for key in keys:
            chunks.append(key + ' = ' + repr(theVars[key])  )
        return '\n'.join(chunks)
        
    def importStatements(self):
        return '\n'.join(self._importStatements)
        
    def moduleConstants(self):
        return '\n'.join(self._moduleConstants)

    def classDefs(self):
        classDefs = [str(klass) for klass in self.finishedClasses() ]
        return '\n\n'.join(classDefs)

    def moduleFooter(self):
        return """
# CHEETAH was developed by Tavis Rudd, Mike Orr, Ian Bicking and Chuck Esterbrook;
# with code, advice and input from many other volunteers.
# For more information visit http://www.CheetahTemplate.org

##################################################
## if run from command line:
if __name__ == '__main__':
    %(className)s().runAsMainProgram()
""" % {'className':self._mainClassName}


##################################################
## Make Compiler an alias for ModuleCompiler
    
Compiler = ModuleCompiler


