#!/usr/bin/env python
# $Id: Compiler.py,v 1.115 2006/01/07 07:12:41 tavis_rudd Exp $
"""Compiler classes for Cheetah:
ModuleCompiler aka 'Compiler'
ClassCompiler
MethodCompiler

If you are trying to grok this code start with ModuleCompiler.__init__,
ModuleCompiler.compile, and ModuleCompiler.__getattr__.

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@damnsimple.com>
Version: $Revision: 1.115 $
Start Date: 2001/09/19
Last Revision Date: $Date: 2006/01/07 07:12:41 $
"""
__author__ = "Tavis Rudd <tavis@damnsimple.com>"
__revision__ = "$Revision: 1.115 $"[11:-2]

import sys
import os
import os.path
from os.path import getmtime, exists
import re
import types
import time
import random
import warnings
import __builtin__

from Cheetah.Version import Version
from Cheetah.SettingsManager import SettingsManager
from Cheetah.Parser import (
    Parser, ParseError, specialVarRE,
    STATIC_CACHE, REFRESH_CACHE,
    SET_LOCAL, SET_GLOBAL,SET_MODULE)
from Cheetah.Utils.Indenter import indentize # an undocumented preprocessor
from Cheetah import ErrorCatchers
from Cheetah import NameMapper

from Cheetah.NameMapper import NotFound, valueForName, valueFromSearchList, valueFromFrameOrSearchList
VFFSL=valueFromFrameOrSearchList
VFSL=valueFromSearchList
VFN=valueForName
currentTime=time.time

class Error(Exception):
    pass

class GenUtils:
    """An abstract baseclass for the Compiler classes that provides methods that
    perform generic utility functions or generate pieces of output code from
    information passed in by the Parser baseclass.  These methods don't do any
    parsing themselves.
    """


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

    def genCacheInfo(self, cacheTokenParts):
        """Decipher a placeholder cachetoken
        """
        
        cacheInfo = {}
        if cacheTokenParts['REFRESH_CACHE']:
            cacheInfo['type'] = REFRESH_CACHE
            cacheInfo['interval'] = self.genTimeInterval(cacheTokenParts['interval'])
        elif cacheTokenParts['STATIC_CACHE']:
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
        if nameChunks[0][0] in self.setting('gettextTokens'):
            self.addGetTextVar(nameChunks) 
        if self.setting('useNameMapper') and not plain:
            return self.genNameMapperVar(nameChunks)
        else:
            return self.genPlainVar(nameChunks)

    def addGetTextVar(self, nameChunks):
        """Output something that gettext can recognize.
        
        This is a harmless side effect necessary to make gettext work when it
        is scanning compiled templates for strings marked for translation.

        @@TR: another marginally more efficient approach would be to put the
        output in a dummy method that is never called.
        """
        # @@TR: this should be in the compiler not here
        self.addChunk("if False:")
        self.indent()
        self.addChunk(self.genPlainVar(nameChunks[:]))
        self.dedent()


    def genPlainVar(self, nameChunks):        
        """Generate Python code for a Cheetah $var without using NameMapper
        (Unified Dotted Notation with the SearchList).
        """
        
        nameChunks.reverse()
        chunk = nameChunks.pop()
        pythonCode = chunk[0] + chunk[2]
        
        while nameChunks:
            chunk = nameChunks.pop()
            pythonCode = (pythonCode + '.' + chunk[0] + chunk[2])
                    
        return pythonCode

    def genNameMapperVar(self, nameChunks):
        """Generate valid Python code for a Cheetah $var, using NameMapper
        (Unified Dotted Notation with the SearchList).

        nameChunks = list of var subcomponents represented as tuples
          [ (name,useAC,remainderOfExpr),
          ]
        where:
          name = the dotted name base
          useAC = where NameMapper should use autocalling on namemapperPart
          remainderOfExpr = any arglist, index, or slice

        If remainderOfExpr contains a call arglist (e.g. '(1234)') then useAC
        is False, otherwise it defaults to True. It is overridden by the global
        setting 'useAutocalling' if this setting is False.

        EXAMPLE
        ------------------------------------------------------------------------
        if the raw Cheetah Var is
          $a.b.c[1].d().x.y.z
          
        nameChunks is the list
          [ ('a.b.c',True,'[1]'), # A
            ('d',False,'()'),     # B
            ('x.y.z',True,''),    # C
          ]
        
        When this method is fed the list above it returns
          VFN(VFN(VFFSL(SL, 'a.b.c',True)[1], 'd',False)(), 'x.y.z',True)
        which can be represented as
          VFN(B`, name=C[0], executeCallables=(useAC and C[1]))C[2]
        where:
          VFN = NameMapper.valueForName
          VFFSL = NameMapper.valueFromFrameOrSearchList
          VFSL = NameMapper.valueFromSearchList # optionally used instead of VFFSL
          SL = self.searchList()
          useAC = self.setting('useAutocalling') # True in this example
          
          A = ('a.b.c',True,'[1]')
          B = ('d',False,'()')
          C = ('x.y.z',True,'')

          C` = VFN( VFN( VFFSL(SL, 'a.b.c',True)[1],
                         'd',False)(),
                    'x.y.z',True)
             = VFN(B`, name='x.y.z', executeCallables=True)
             
          B` = VFN(A`, name=B[0], executeCallables=(useAC and B[1]))B[2]
          A` = VFFSL(SL, name=A[0], executeCallables=(useAC and A[1]))A[2]


        Note, if the compiler setting useStackFrames=False (default is true)
        then
          A` = VFSL([locals()]+SL+[globals(), __builtin__], name=A[0], executeCallables=(useAC and A[1]))A[2]
        This option allows Cheetah to be used with Psyco, which doesn't support
        stack frame introspection.
        """

        defaultUseAC = self.setting('useAutocalling')
        useSearchList = self.setting('useSearchList')

        nameChunks.reverse()
        name, useAC, remainder = nameChunks.pop()

        if not useSearchList:
            firstDotIdx = name.find('.')
            if firstDotIdx != -1 and firstDotIdx < len(name):
                beforeFirstDot, afterDot = name[:firstDotIdx], name[firstDotIdx+1:]
                pythonCode = ('VFN(' + beforeFirstDot +
                              ',"' + afterDot +
                              '",' + repr(defaultUseAC and useAC) + ')'
                              + remainder)
                #print 'DEBUG1: ', pythonCode, name, remainder
            else:
                pythonCode = name+remainder
                #print 'DEBUG2: ', pythonCode, name, remainder

        elif self.setting('useStackFrames'):
            pythonCode = ('VFFSL(SL,'
                          '"'+ name + '",'
                          + repr(defaultUseAC and useAC) + ')'
                          + remainder)
        else:
            pythonCode = ('VFSL([locals()]+SL+[globals(), __builtin__],'
                          '"'+ name + '",'
                          + repr(defaultUseAC and useAC) + ')'
                          + remainder)
            
        while nameChunks:
            name, useAC, remainder = nameChunks.pop()
            pythonCode = ('VFN(' + pythonCode +
                          ',"' + name +
                          '",' + repr(defaultUseAC and useAC) + ')'
                          + remainder)
        return pythonCode
    
##################################################
## METHOD COMPILERS

class MethodCompiler(GenUtils):
    def __init__(self, methodName, classCompiler,
                 initialMethodComment=None,
                 templateObj=None):
        self._settingsManager = classCompiler
        self._classCompiler = classCompiler
        self._moduleCompiler = classCompiler._moduleCompiler
        self._templateObj = templateObj
        self._methodName = methodName
        self._initialMethodComment = initialMethodComment
        self._setupState()

    def setting(self, key):
        return self._settingsManager.setting(key)

    def _setupState(self):
        self._indent = self.setting('indentationStep')
        self._indentLev = self.setting('initialMethIndentLevel')
        self._pendingStrConstChunks = []
        self._methodSignature = None
        self._methodDef = None
        self._docStringLines = []
        self._methodBodyChunks = []

        self._cacheRegionOpen = False
        self._cacheRegionsStack = []
        self._callRegionsStack = []

        self._isErrorCatcherOn = False

        self._hasReturnStatement = False
        self._isGenerator = False
        
        
    def cleanupState(self):
        """Called by the containing class compiler instance
        """
        pass

    def methodName(self):
        return self._methodName

    def setMethodName(self, name):
        self._methodName = name
        
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
        if not self._docStringLines:
            return ''
        
        ind = self._indent*2        
        docStr = (ind + '"""\n' + ind +
                  ('\n' + ind).join(ln.replace('"""',"'''") for ln in self._docStringLines) +
                  '\n' + ind + '"""\n')
        return  docStr

    ## methods for adding code

    def addMethDocString(self, line):
        self._docStringLines.append(line.replace('%','%%'))
       
    def addChunk(self, chunk):
        self.commitStrConst()
        chunk = "\n" + self.indentation() + chunk
        self._methodBodyChunks.append(chunk)

    def appendToPrevChunk(self, appendage):
        self._methodBodyChunks[-1] = self._methodBodyChunks[-1] + appendage

    def addWriteChunk(self, chunk):
        self.addChunk('write(' + chunk + ')')

    def addFilteredChunk(self, chunk, filterArgs=None, rawExpr=None):
        if filterArgs is None:
            filterArgs = ''
        if self.setting('includeRawExprInFilterArgs') and rawExpr:
            filterArgs += ', rawExpr=%s'%repr(rawExpr)

        if self.setting('alwaysFilterNone'):
            if rawExpr and rawExpr.find('\n')==-1 and rawExpr.find('\r')==-1:
                self.addChunk("_v = %s # %s"%(chunk, rawExpr))
            else:
                self.addChunk("_v = %s"%chunk)
                
            if self.setting('useFilters'):
                self.addChunk("if _v is not None: write(_filter(_v%s))"%filterArgs)
            else:
                self.addChunk("if _v is not None: write(str(_v))")
        else:
            
            if self.setting('useFilters'):
                self.addChunk("write(_filter(%s%s))"%(chunk,filterArgs))
            else:
                self.addChunk("write(str(%s))"%chunk)



    def _appendToPrevStrConst(self, strConst):
        if self._pendingStrConstChunks:
            self._pendingStrConstChunks.append(strConst)
        else:
            self._pendingStrConstChunks = [strConst]

    def _unescapeCheetahVars(self, theString):
        """Unescape any escaped Cheetah \$vars in the string.
        """
        
        token = self.setting('cheetahVarStartToken')
        return theString.replace('\\' + token, token)

    def _unescapeDirectives(self, theString):
        """Unescape any escaped Cheetah \$vars in the string.
        """
        
        token = self.setting('directiveStartToken')
        return theString.replace('\\' + token, token)
        
    def commitStrConst(self):
        """Add the code for outputting the pending strConst without chopping off
        any whitespace from it.
        """
        if self._pendingStrConstChunks:
            strConst = self._unescapeCheetahVars(''.join(self._pendingStrConstChunks))
            strConst = self._unescapeDirectives(strConst)
            self._pendingStrConstChunks = []
            if not strConst:
                return
            if self.setting('reprShortStrConstants') and \
               strConst.count('\n') < self.setting('reprNewlineThreshold'):
                self.addWriteChunk( repr(strConst).replace('\\012','\\n'))
            else:
                strConst = strConst.replace('\\','\\\\').replace("'''","'\'\'\'")
                if strConst[0] == "'":
                    strConst = '\\' + strConst
                if strConst[-1] == "'":
                    strConst = strConst[:-1] + '\\' + strConst[-1]
                    
                self.addWriteChunk("'''" + strConst + "'''" )

    def handleWSBeforeDirective(self):
        """Truncate the pending strCont to the beginning of the current line.
        """
        if self._pendingStrConstChunks:
            src = self._pendingStrConstChunks[-1]
            BOL = max(src.rfind('\n')+1, src.rfind('\r')+1, 0)
            if BOL < len(src):
                self._pendingStrConstChunks[-1] = src[:BOL]



    def isErrorCatcherOn(self):
        return self._isErrorCatcherOn
    
    def turnErrorCatcherOn(self):
        self._isErrorCatcherOn = True

    def turnErrorCatcherOff(self):
        self._isErrorCatcherOn = False
            
    # @@TR: consider merging the next two methods into one
    def addStrConst(self, strConst):
        self._appendToPrevStrConst(strConst)

    def addRawText(self, text):
        self.addStrConst(text)
        
    def addMethComment(self, comm):
        offSet = self.setting('commentOffset')
        self.addChunk('#' + ' '*offSet + comm)

    def addPlaceholder(self, expr, filterArgs, rawPlaceholder, cacheTokenParts, lineCol):
        cacheInfo = self.genCacheInfo(cacheTokenParts)
        if cacheInfo:
            cacheInfo['ID'] = repr(rawPlaceholder)[1:-1]
            self.startCacheRegion(cacheInfo, lineCol, rawPlaceholder=rawPlaceholder)

        if self.isErrorCatcherOn():
            methodName = self._classCompiler.addErrorCatcherCall(
                expr, rawCode=rawPlaceholder, lineCol=lineCol)
            expr = 'self.' + methodName + '(localsDict=locals())' 
        self.addFilteredChunk(expr, filterArgs, rawPlaceholder)      
        if self.setting('outputRowColComments'):
            self.appendToPrevChunk(' # from line %s, col %s' % lineCol + '.')
        if cacheInfo:
            self.endCacheRegion()

    def addSilent(self, expr):
        self.addChunk( expr )

    def addEcho(self, expr, rawExpr=None):
        self.addFilteredChunk(expr, rawExpr=rawExpr)
        
    def addSet(self, expr, exprComponents, setStyle):
        if setStyle is SET_GLOBAL:
            (LVALUE, OP, RVALUE) = (exprComponents.LVALUE,
                                    exprComponents.OP,
                                    exprComponents.RVALUE
                                    )
            # we need to split the LVALUE to deal with globalSetVars
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
            LVALUE = 'self._CHEETAH_globalSetVars["' + primary + '"]' + secondary
            expr = LVALUE + ' ' + OP + ' ' + RVALUE.strip()

        if setStyle is SET_MODULE:
            #self._moduleCompiler.addModuleHeader(expr)
            self._moduleCompiler.addModuleGlobal(expr)
            #self._moduleCompiler.addSpecialVar(
            #    LVALUE, RVALUE.strip(), includeUnderscores=False)
        else:
            self.addChunk(expr)

    def addInclude(self, sourceExpr, includeFrom, isRaw):
        # @@TR: consider soft-coding this
        self.addChunk('self._includeCheetahSource(' + sourceExpr +
                           ', trans=trans, ' +
                           'includeFrom="' + includeFrom + '", raw=' +
                           repr(isRaw) + ')')

    def addWhile(self, expr):
        self.addIndentingDirective(expr)
        
    def addFor(self, expr):
        self.addIndentingDirective(expr)

    #def closeFor(self)
    #    self._compiler.commitStrConst()
    #    self._compiler.dedent()

    def addRepeat(self, expr):
        #the _repeatCount stuff here allows nesting of #repeat directives        
        self._repeatCount = getattr(self, "_repeatCount", -1) + 1
        self.addFor('for __i%s in range(%s)' % (self._repeatCount,expr))

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
        """For a full #if ... #end if directive
        """
        self.addIndentingDirective(expr)

    def addOneLineIf(self, conditionExpr, trueExpr, falseExpr):
        """For a single-lie #if ... then .... else ... directive
        <condition> then <trueExpr> else <falseExpr>
        """
        self.addIndentingDirective(conditionExpr)            
        self.addFilteredChunk(trueExpr)
        self.dedent()
        self.addIndentingDirective('else')            
        self.addFilteredChunk(falseExpr)
        self.dedent()

    def addElse(self, expr):
        expr = re.sub(r'else[ \f\t]+if','elif', expr)
        self.addReIndentingDirective(expr)

    def addUnless(self, expr):
        self.addIf('if not (' + expr + ')')

    def addClosure(self, functionName, argsList, parserComment):
        argStringChunks = []
        for arg in argsList:
            chunk = arg[0]
            if not arg[1] == None:
                chunk += '=' + arg[1]
            argStringChunks.append(chunk)
        signature = "def " + functionName + "(" + ','.join(argStringChunks) + "):"
        self.addIndentingDirective(signature)
        self.addChunk('#'+parserComment)

    def addTry(self, expr):
        self.addIndentingDirective(expr)
        
    def addExcept(self, expr):
        self.addReIndentingDirective(expr)
        
    def addFinally(self, expr):
        self.addReIndentingDirective(expr)
            
    def addReturn(self, expr):
        assert not self._isGenerator
        self.addChunk(expr)
        self._hasReturnStatement = True

    def addYield(self, expr):
        assert not self._hasReturnStatement
        self._isGenerator = True
        if expr.replace('yield','').strip():
            self.addChunk(expr)
        else:
            self.addChunk('if _dummyTrans:')
            self.indent()
            self.addChunk('yield trans.response().getvalue()')
            self.addChunk('trans = DummyTransaction()')
            self.addChunk('write = trans.response().write')
            self.dedent()
            self.addChunk('else:')
            self.indent()
            self.addChunk(
                'raise TypeError("This method cannot be called with a trans arg")')
            self.dedent()
            

    def addPass(self, expr):
        self.addChunk(expr)

    def addDel(self, expr):
        self.addChunk(expr)

    def addAssert(self, expr):
        self.addChunk(expr)

    def addRaise(self, expr):
        self.addChunk(expr)

    def addBreak(self, expr):
        self.addChunk(expr)

    def addContinue(self, expr):
        self.addChunk(expr)

    def addPSP(self, PSP):
        self.commitStrConst()
        autoIndent = False
        if PSP[0] == '=':
            PSP = PSP[1:]
            if PSP:
                self.addWriteChunk('_filter(' + PSP + ')')
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
    
    def nextCacheID(self):
        return ('_'+str(random.randrange(100, 999)) 
                + str(random.randrange(10000, 99999)))
        
    def startCacheRegion(self, cacheInfo, lineCol, rawPlaceholder=None):
        ID = self.nextCacheID()
        interval = cacheInfo.get('interval',None)
        test = cacheInfo.get('test',None)
        
        customID = cacheInfo.get('id',None)
        if customID:
            ID = customID
        varyBy = cacheInfo.get('varyBy',repr(ID))
        
        self._cacheRegionsStack.append(ID) # attrib of current methodCompiler
        
        self.addChunk('## START CACHE REGION: '+ID+
                      '. line, col ' + str(lineCol) + ' in the source.')
        self.addChunk('_RECACHE%(ID)s = False'%locals())

        self.addChunk('_cacheRegion%(ID)s = self._CHEETAH_cacheRegions.get('%locals()
                      + repr(ID) + ')')
        
        self.addChunk('if not _cacheRegion%(ID)s:'%locals())
        self.indent()
        self.addChunk("_cacheRegion%(ID)s = CacheRegion()"%locals())
        self.addChunk("self._CHEETAH_cacheRegions[" + repr(ID)
                      + "] = _cacheRegion%(ID)s"%locals())
        self.addChunk('_RECACHE%(ID)s = True'%locals())
        self.dedent()
        
        self.addChunk('_cache%(ID)s = _cacheRegion%(ID)s.getCache('%locals()
                      +varyBy+')')

        if interval:
            #self.addMethDocString(
            #    'Contains a cache region which will be refreshed every ' +
            #    str(interval) + ' seconds.'
            #    +(rawPlaceholder and ' %s'%rawPlaceholder or ''))
                
            self.addChunk(('if (not _cache%(ID)s.getRefreshTime())'%locals())
                          +' or (currentTime() > cache.getRefreshTime()):')
            self.indent()
            self.addChunk(("_cache%(ID)s.setRefreshTime(currentTime() +"%locals())
                          + str(interval) + ")")
            self.addChunk('_RECACHE%(ID)s = True'%locals())
            self.dedent()
            
        if test:
            self.addChunk('if ' + test + ':')
            self.indent()
            self.addChunk('_RECACHE%(ID)s = True'%locals())
            self.dedent()
            
        self.addChunk('if _RECACHE%(ID)s or not _cache%(ID)s.getData():'%locals())
        self.indent()
        self.addChunk('_orig_trans%(ID)s = trans'%locals())
        self.addChunk('trans = _cacheCollector%(ID)s = DummyTransaction()'%locals())
        self.addChunk('write = _cacheCollector%(ID)s.response().write'%locals())
        
    def endCacheRegion(self):
        ID = self._cacheRegionsStack.pop()
        self.addChunk('trans = _orig_trans%(ID)s'%locals())
        self.addChunk('write = trans.response().write')
        self.addChunk(
            '_cache%(ID)s.setData(_cacheCollector%(ID)s.response().getvalue())'%locals())
        self.addChunk('del _cacheCollector%(ID)s'%locals())
        
        self.dedent()        
        self.addWriteChunk('_cache%(ID)s.getData()'%locals())
        self.addChunk('## END CACHE REGION: '+ID)
        self.addChunk('')


    def nextCallRegionID(self):
        return self.nextCacheID()

    def startCallRegion(self, functionName, args, lineCol):
        class CallDetails: pass
        callDetails = CallDetails()
        callDetails.ID = ID = self.nextCallRegionID()
        callDetails.functionName = functionName
        callDetails.args = args
        callDetails.lineCol = lineCol
        callDetails.usesKeywordArgs = False
        self._callRegionsStack.append((ID, callDetails)) # attrib of current methodCompiler

        self.addChunk('## START CALL REGION: '+ID
                      +' of '+functionName
                      +' at line, col ' + str(lineCol) + ' in the source.')
        self.addChunk('_orig_trans%(ID)s = trans'%locals())
        self.addChunk('trans = _callCollector%(ID)s = DummyTransaction()'%locals())
        self.addChunk('write = _callCollector%(ID)s.response().write'%locals())

    def setCallArg(self, argName, lineCol):
        ID, callDetails = self._callRegionsStack[-1]
        if callDetails.usesKeywordArgs:
            self._endCallArg()
        else:
            callDetails.usesKeywordArgs = True
            self.addChunk('_callKws%(ID)s = {}'%locals())
            self.addChunk('_currentCallArgname%(ID)s = %(argName)r'%locals())
        callDetails.currentArgname = argName
        
    def _endCallArg(self):
        ID, callDetails = self._callRegionsStack[-1]
        currCallArg = callDetails.currentArgname
        self.addChunk(('_callKws%(ID)s[%(currCallArg)r] ='
                       ' _callCollector%(ID)s.response().getvalue()')%locals())
        self.addChunk('del _callCollector%(ID)s'%locals())
        self.addChunk('trans = _callCollector%(ID)s = DummyTransaction()'%locals())
        self.addChunk('write = _callCollector%(ID)s.response().write'%locals())
    
    def endCallRegion(self):
        ID, callDetails = self._callRegionsStack[-1]
        functionName, initialKwArgs, lineCol = (callDetails.functionName,
                                                callDetails.args,
                                                callDetails.lineCol)
        if not callDetails.usesKeywordArgs:
            self.addChunk('trans = _orig_trans%(ID)s'%locals())
            self.addChunk('write = trans.response().write')
            self.addChunk('_callArgVal%(ID)s = _callCollector%(ID)s.response().getvalue()'%locals())
            self.addChunk('del _callCollector%(ID)s'%locals())
            if initialKwArgs:
                initialKwArgs = ', '+initialKwArgs           
            self.addFilteredChunk('%(functionName)s(_callArgVal%(ID)s%(initialKwArgs)s)'%locals())
            self.addChunk('del _callArgVal%(ID)s'%locals())
        else:
            if initialKwArgs:
                initialKwArgs = initialKwArgs+', '
            self._endCallArg()
            self.addChunk('trans = _orig_trans%(ID)s'%locals())
            self.addChunk('write = trans.response().write')            
            self.addFilteredChunk('%(functionName)s(%(initialKwArgs)s**_callKws%(ID)s)'%locals())
            self.addChunk('del _callKws%(ID)s'%locals())
        self.addChunk('## END CALL REGION: '+ID
                      +' of '+functionName
                      +' at line, col ' + str(lineCol) + ' in the source.')        
        self.addChunk('')
        self._callRegionsStack.pop() # attrib of current methodCompiler

    def setErrorCatcher(self, errorCatcherName):
        self.turnErrorCatcherOn()        
        if self._templateObj:
            self._templateObj._CHEETAH_errorCatcher = \
                   getattr(ErrorCatchers, errorCatcherName)(self._templateObj)

        self.addChunk('if self._CHEETAH_errorCatchers.has_key("' + errorCatcherName + '"):')
        self.indent()
        self.addChunk('self._CHEETAH_errorCatcher = self._CHEETAH_errorCatchers["' +
            errorCatcherName + '"]')
        self.dedent()
        self.addChunk('else:')
        self.indent()
        self.addChunk('self._CHEETAH_errorCatcher = self._CHEETAH_errorCatchers["'
                      + errorCatcherName + '"] = ErrorCatchers.'
                      + errorCatcherName + '(self)'
                      )
        self.dedent()
        
    def setFilter(self, theFilter, isKlass):
        if isKlass:
            self.addChunk('_filter = self._CHEETAH_currentFilter = ' + theFilter.strip() +
                          '(self).filter')
        else:
            if theFilter.lower() == 'none':
                self.addChunk('_filter = self._CHEETAH_initialFilter')
            else:
                # is string representing the name of a builtin filter
                self.addChunk('filterName = ' + repr(theFilter))
                self.addChunk('if self._CHEETAH_filters.has_key("' + theFilter + '"):')
                self.indent()
                self.addChunk('_filter = self._CHEETAH_currentFilter = self._CHEETAH_filters[filterName]')
                self.dedent()
                self.addChunk('else:')
                self.indent()
                self.addChunk('_filter = self._CHEETAH_currentFilter'
                              +' = \\\n\t\t\tself._CHEETAH_filters[filterName] = '
                              + 'getattr(self._CHEETAH_filtersLib, filterName)(self).filter')
                self.dedent()
                
    def closeFilterBlock(self):
        self.addChunk('_filter = self._CHEETAH_initialFilter')        

class AutoMethodCompiler(MethodCompiler):

    def _setupState(self):
        MethodCompiler._setupState(self)
        self._argStringList = [ ("self",None) ]
        self._streamingEnabled = True

    def _useKWsDictArgForPassingTrans(self):
        alreadyHasTransArg = [argname for argname,defval in self._argStringList
                              if argname=='trans']
        return (self.methodName()!='respond'
                and not alreadyHasTransArg
                and self.setting('useKWsDictArgForPassingTrans'))
    
    def cleanupState(self):
        MethodCompiler.cleanupState(self)
        self.commitStrConst()
        if self._cacheRegionsStack:
            self.endCacheRegion()
        if self._callRegionsStack:
            self.endCallRegion()
            
        if self._streamingEnabled:
            kwargsName = None
            positionalArgsListName = None
            for argname,defval in self._argStringList:
                if argname.strip().startswith('**'):
                    kwargsName = argname.strip().replace('**','')
                    break
                elif argname.strip().startswith('*'):
                    positionalArgsListName = argname.strip().replace('*','')
                    
            if not kwargsName and self._useKWsDictArgForPassingTrans():
                kwargsName = 'KWS'
                self.addMethArg('**KWS', None)
            self._kwargsName = kwargsName

            if not self._useKWsDictArgForPassingTrans():
                if not kwargsName and not positionalArgsListName:
                    self.addMethArg('trans', 'None')       
                else:
                    self._streamingEnabled = False
            #if self._streamingEnabled and self.setting('useNameMapper'):
            #    argList.extend([("VFFSL","valueFromFrameOrSearchList"), 
            #                    ("VFN","valueForName")])                
                
        self._indentLev = self.setting('initialMethIndentLevel')
        mainBodyChunks = self._methodBodyChunks
        self._methodBodyChunks = []
        self._addAutoSetupCode()
        self._methodBodyChunks.extend(mainBodyChunks)
        self._addAutoCleanupCode()
        
    def _addAutoSetupCode(self):
        if self._initialMethodComment:
            self.addChunk(self._initialMethodComment)
            
        if self._streamingEnabled:
            if self._useKWsDictArgForPassingTrans() and self._kwargsName:
                self.addChunk('trans = %s.get("trans")'%self._kwargsName)            
            self.addChunk('if not trans and not callable(self.transaction):')
            self.indent()
            self.addChunk('trans = self.transaction'
                          ' # is None unless self.awake() was called')
            self.dedent()

            self.addChunk('if not trans:')
            self.indent()
            self.addChunk('trans = DummyTransaction()')
            if self.setting('autoAssignDummyTransactionToSelf'):
                self.addChunk('self.transaction = trans')            
            self.addChunk('_dummyTrans = True')
            self.dedent()
            self.addChunk('else: _dummyTrans = False')

        else:
            self.addChunk('trans = DummyTransaction()')
            self.addChunk('_dummyTrans = True')
        self.addChunk('write = trans.response().write')
        if self.setting('useNameMapper'):
            argNames = [arg[0] for arg in self._argStringList]
            allowSearchListAsMethArg = self.setting('allowSearchListAsMethArg')            
            if allowSearchListAsMethArg and 'SL' in argNames:
                pass
            elif allowSearchListAsMethArg and 'searchList' in argNames:
                self.addChunk('SL = searchList')
            else:
                self.addChunk('SL = self._CHEETAH_searchList')                
        if self.setting('useFilters'):
            self.addChunk('_filter = self._CHEETAH_currentFilter')
        self.addChunk('')

        self.addChunk("#" *40)
        self.addChunk('## START - generated method body')
        self.addChunk('')

    def _addAutoCleanupCode(self):
        self.addChunk('')
        self.addChunk("#" *40)
        self.addChunk('## END - generated method body')
        self.addChunk('')

        if not self._isGenerator:
            self.addStop()
        self.addChunk('')
        
    def addStop(self, expr=None):
        self.addChunk('return _dummyTrans and trans.response().getvalue() or ""')

    def addMethArg(self, name, defVal=None):
        asteriskPos = max(name.rfind('*')+1, 0)
        #if asteriskPos:
        #    self._streamingEnabled = False
        self._argStringList.append( (name,defVal) )
        
    def methodSignature(self):
        argStringChunks = []
        for arg in self._argStringList:
            chunk = arg[0]
            if not arg[1] == None:
                chunk += '=' + arg[1]
            argStringChunks.append(chunk)
        argString = (', ').join(argStringChunks)
        return (self._indent + "def " + self.methodName() + "(" +
                 argString + "):\n\n")


##################################################
## CLASS COMPILERS

_initMethod_initCheetah = """\
if not self._CHEETAH_instanceInitialized:
    cheetahKWArgs = {}
    allowedKWs = 'searchList filter filtersLib errorCatcher'.split()
    for k,v in KWs.items():
        if k in allowedKWs: cheetahKWArgs[k] = v
    self._initCheetahAttributes(**cheetahKWArgs)
""".replace('\n','\n'+' '*8)

class ClassCompiler(GenUtils):
    methodCompilerClass = AutoMethodCompiler
    methodCompilerClassForInit = MethodCompiler
        
    def __init__(self, className, mainMethodName='respond',
                 moduleCompiler=None,
                 templateObj=None,
                 fileName=None,
                 settingsManager=None):

        self._settingsManager = settingsManager
        self._fileName = fileName
        self._className = className
        self._moduleCompiler = moduleCompiler
        self._mainMethodName = mainMethodName
        self._templateObj = templateObj
        self._setupState()
        methodCompiler = self._spawnMethodCompiler(
            mainMethodName,
            initialMethodComment='## CHEETAH: main method generated for this template')
        self._setActiveMethodCompiler(methodCompiler)
        if fileName and self.setting('monitorSrcFile'):
            self._addSourceFileMonitoring(fileName)

    def setting(self, key):
        return self._settingsManager.setting(key)

    def __getattr__(self, name):
        """Provide access to the methods and attributes of the MethodCompiler
        at the top of the activeMethods stack: one-way namespace sharing

        
        WARNING: Use .setMethods to assign the attributes of the MethodCompiler
        from the methods of this class!!! or you will be assigning to attributes
        of this object instead."""
        
        if self.__dict__.has_key(name):
            return self.__dict__[name]
        elif hasattr(self.__class__, name):
            return getattr(self.__class__, name)
        elif self._activeMethodsList and hasattr(self._activeMethodsList[-1], name):
            return getattr(self._activeMethodsList[-1], name)
        else:
            raise AttributeError, name

    def _setupState(self):
        self._classDef = None
        self._activeMethodsList = []        # stack while parsing/generating
        self._finishedMethodsList = []      # store by order
        self._methodsIndex = {}      # store by name
        self._baseClass = 'Template'
        self._classDocStringLines = []
        # printed after methods in the gen class def:
        self._generatedAttribs = ['_CHEETAH_instanceInitialized = False']
        if self.setting('templateMetaclass'):
            self._generatedAttribs.append('__metaclass__ = '+self.setting('templateMetaclass'))
        self._initMethChunks = []
        
        self._blockMetaData = {}
        self._errorCatcherCount = 0
        self._placeholderToErrorCatcherMap = {}

    def cleanupState(self):
        while self._activeMethodsList:
            methCompiler = self._popActiveMethodCompiler()
            self._swallowMethodCompiler(methCompiler)
        self._setupInitMethod()
        if self._mainMethodName == 'respond':
            if self.setting('setup__str__method'):
                self._generatedAttribs.append('def __str__(self): return self.respond()')
            if self._templateObj:
                self._templateObj.__str__ = self._templateObj.respond
        self.addAttribute('_mainCheetahMethod_for_' + self._className +
                           '= ' + repr(self._mainMethodName)
                           )

    def _setupInitMethod(self):
        __init__ = self._spawnMethodCompiler('__init__',
                                             klass=self.methodCompilerClassForInit)
        __init__.setMethodSignature("def __init__(self, *args, **KWs)")
        __init__.addChunk("%s.__init__(self, *args, **KWs)" % self._baseClass)
        __init__.addChunk(_initMethod_initCheetah%dict(className=self._className))
        for chunk in self._initMethChunks:
            __init__.addChunk(chunk)
        __init__.cleanupState()
        self._swallowMethodCompiler(__init__, pos=0)

    def _addSourceFileMonitoring(self, fileName):
        # the first bit is added to init
        self.addChunkToInit('self._filePath = ' + repr(fileName))
        self.addChunkToInit('self._fileMtime = ' + str(getmtime(fileName)) )
        if self._templateObj:
            setattr(self._templateObj, '_filePath', fileName)
            setattr(self._templateObj, '_fileMtime', getmtime(fileName))

        # the rest is added to the main output method of the class ('mainMethod')
        self.addChunk('if exists(self._filePath) and ' +
                      'getmtime(self._filePath) > self._fileMtime:')
        self.indent()
        self.addChunk('self.compile(file=self._filePath, moduleName='
                      +className + ')')
        self.addChunk(
            'write(getattr(self, self._mainCheetahMethod_for_' + self._className +
            ')(trans=trans))')            
        self.addStop()
        self.dedent()

    
    def setClassName(self, name):
        self._className = name

    def className(self):
        return self._className

    def setBaseClass(self, baseClassName):
        self._baseClass = baseClassName
               
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
        
    
    def _spawnMethodCompiler(self, methodName, klass=None, 
                             initialMethodComment=None):
        if klass is None:
            klass = self.methodCompilerClass
        methodCompiler = klass(methodName, classCompiler=self,
                               initialMethodComment=initialMethodComment,
                               templateObj=self._templateObj)
        self._methodsIndex[methodName] = methodCompiler
        return methodCompiler

    def _setActiveMethodCompiler(self, methodCompiler):
        self._activeMethodsList.append(methodCompiler)

    def _getActiveMethodCompiler(self):
        return self._activeMethodsList[-1]

    def _popActiveMethodCompiler(self):
        return self._activeMethodsList.pop()

    def _swallowMethodCompiler(self, methodCompiler, pos=None):
        methodCompiler.cleanupState()
        if pos==None:
            self._finishedMethodsList.append( methodCompiler )
        else:
            self._finishedMethodsList.insert(pos, methodCompiler)

        if self._templateObj and methodCompiler.methodName() != '__init__':
            self._templateObj._bindCompiledMethod(methodCompiler)
        return methodCompiler


    def startMethodDef(self, methodName, argsList, parserComment):
        methodCompiler = self._spawnMethodCompiler(
            methodName, initialMethodComment=parserComment)
        self._setActiveMethodCompiler(methodCompiler)        
        for argName, defVal in argsList:
            methodCompiler.addMethArg(argName, defVal)
        
    def _finishedMethods(self):
        return self._finishedMethodsList

    def addClassDocString(self, line):
        self._classDocStringLines.append( line.replace('%','%%')) 

    def addChunkToInit(self,chunk):
        self._initMethChunks.append(chunk)

    def addAttribute(self, attribExpr):
        ## first test to make sure that the user hasn't used any fancy Cheetah syntax
        #  (placeholders, directives, etc.) inside the expression 
        if attribExpr.find('VFN(') != -1 or attribExpr.find('VFFSL(') != -1:
            raise ParseError(self,
                             'Invalid #attr directive.' +
                             ' It should only contain simple Python literals.')
        ## now add the attribute
        self._generatedAttribs.append(attribExpr)
        if self._templateObj:
            exec('self._templateObj.' + attribExpr.strip())

    def addSettingsToInit(self, settingsStr, settingsType='ini'):
        #@@TR 2005-01-01: this may not be used anymore?
        if settingsType=='python':
            reader = 'updateSettingsFromPySrcStr'
        else:            
            reader = 'updateSettingsFromConfigStr'

        settingsCode = ("self." + reader + "('''" +
                        settingsStr.replace("'''","\'\'\'") +
                        "''')")
        self.addChunkToInit(settingsCode)

    def addErrorCatcherCall(self, codeChunk, rawCode='', lineCol=''):
        if self._placeholderToErrorCatcherMap.has_key(rawCode):
            methodName = self._placeholderToErrorCatcherMap[rawCode]
            if not self.setting('outputRowColComments'):
                self._methodsIndex[methodName].addMethDocString(
                    'plus at line, col ' + str(lineCol))
            return methodName

        self._errorCatcherCount += 1
        methodName = '__errorCatcher' + str(self._errorCatcherCount)
        self._placeholderToErrorCatcherMap[rawCode] = methodName
        
        catcherMeth = self._spawnMethodCompiler(
            methodName,
            klass=MethodCompiler,
            initialMethodComment=('## CHEETAH: Generated from ' + rawCode +
                                  ' at line, col ' + str(lineCol) + '.')
            )        
        catcherMeth.setMethodSignature('def ' + methodName +
                                       '(self, localsDict={})')
                                        # is this use of localsDict right?
        catcherMeth.addChunk('try:')
        catcherMeth.indent()
        catcherMeth.addChunk("return eval('''" + codeChunk +
                             "''', globals(), localsDict)")
        catcherMeth.dedent()
        catcherMeth.addChunk('except self._CHEETAH_errorCatcher.exceptions(), e:')
        catcherMeth.indent()        
        catcherMeth.addChunk("return self._CHEETAH_errorCatcher.warn(exc_val=e, code= " +
                             repr(codeChunk) + " , rawCode= " +
                             repr(rawCode) + " , lineCol=" + str(lineCol) +")")
        
        catcherMeth.cleanupState()
        
        self._swallowMethodCompiler(catcherMeth)
        return methodName

    def closeDef(self):
        self.commitStrConst()
        methCompiler = self._popActiveMethodCompiler()
        self._swallowMethodCompiler(methCompiler)

    def closeBlock(self):
        self.commitStrConst()
        methCompiler = self._popActiveMethodCompiler()
        methodName = methCompiler.methodName()
        if self.setting('includeBlockMarkers'):
            endMarker = self.setting('blockMarkerEnd')
            methCompiler.addStrConst(endMarker[0] + methodName + endMarker[1])
        self._swallowMethodCompiler(methCompiler)
        
        #metaData = self._blockMetaData[methodName] 
        #rawDirective = metaData['raw']
        #lineCol = metaData['lineCol']
        
        ## insert the code to call the block, caching if #cache directive is on
        codeChunk = 'self.' + methodName + '(trans=trans)'
        self.addChunk(codeChunk)
        
        #self.appendToPrevChunk(' # generated from ' + repr(rawDirective) )
        #if self.setting('outputRowColComments'):
        #    self.appendToPrevChunk(' at line %s, col %s' % lineCol + '.')


    ## code wrapping methods
    
    def classDef(self):
        if self._classDef:
            return self._classDef
        else:
            return self.wrapClassDef()

    __str__ = classDef
    
    def wrapClassDef(self):
        ind = self.setting('indentationStep')
        classDefChunks = [self.classSignature(),
                          self.classDocstring(),
                          ]
        def addMethods():
            classDefChunks.extend([
                ind + '#'*50,
                ind + '## CHEETAH GENERATED METHODS',
                '\n',
                self.methodDefs(),
                ])
        def addAttributes():
            classDefChunks.extend([
                ind + '#'*50,
                ind + '## CHEETAH GENERATED ATTRIBUTES',
                '\n',
                self.attributes(),
                ])            
        if self.setting('outputMethodsBeforeAttributes'):
            addMethods()
            addAttributes()
        else:
            addAttributes()
            addMethods()
            
        classDef = '\n'.join(classDefChunks)
        self._classDef = classDef
        return classDef


    def classSignature(self):
        return "class %s(%s):" % (self.className(), self._baseClass)
        
    def classDocstring(self):
        if not self._classDocStringLines:
            return ''
        ind = self.setting('indentationStep')
        docStr = ('%(ind)s"""\n%(ind)s' +
                  '\n%(ind)s'.join(self._classDocStringLines) +
                  '\n%(ind)s"""\n'
                  ) % {'ind':ind}
        return  docStr

    def methodDefs(self):
        methodDefs = [str(methGen) for methGen in self._finishedMethods() ]
        return '\n\n'.join(methodDefs)

    def attributes(self):
        attribs = [self.setting('indentationStep') + str(attrib)
                      for attrib in self._generatedAttribs ]
        return '\n\n'.join(attribs)

    
class AutoClassCompiler(ClassCompiler):
    pass


##################################################
## MODULE COMPILERS

DEFAULT_COMPILER_SETTINGS = {
    ## controlling the handling of Cheetah $placeholders
    'useNameMapper': True,      # Unified dotted notation and the searchList
    'useSearchList': True,      # if false, assume the first
                                # portion of the $variable (before the first dot) is a global,
                                # builtin, or local var that doesn't need
                                # looking up in the searchlist BUT use
                                # namemapper on the rest of the lookup
    'allowSearchListAsMethArg': True,
    'useAutocalling': True, # detect and call callable()'s, requires NameMapper
    'useStackFrames': True, # use NameMapper.valueFromFrameOrSearchList
    # rather than NameMapper.valueFromSearchList
    'useErrorCatcher':False,

    'autoImportForExtendDirective':True,
    'alwaysFilterNone':True, # filter out None, before the filter is called
    'useFilters':True, # use str instead if =False
    'includeRawExprInFilterArgs':True,
    
    #'lookForTransactionAttr':False,
    'autoAssignDummyTransactionToSelf':False,
    'useKWsDictArgForPassingTrans':True,
    
    ## controlling the aesthetic appearance / behaviour of generated code
    'commentOffset': 1,
    # should shorter str constant chunks be printed using repr rather than ''' quotes
    'reprShortStrConstants': True, 
    'reprNewlineThreshold':3,
    'outputRowColComments':True,
    # should #block's be wrapped in a comment in the template's output
    'includeBlockMarkers': False,   
    'blockMarkerStart':('\n<!-- START BLOCK: ',' -->\n'),
    'blockMarkerEnd':('\n<!-- END BLOCK: ',' -->\n'),           
    'defDocStrMsg':'Autogenerated by CHEETAH: The Python-Powered Template Engine',
    'setup__str__method': True, 
    'mainMethodName':'respond',
    'mainMethodNameForSubclasses':'writeBody',
    'indentationStep': ' '*4,
    'initialMethIndentLevel': 2,
    'monitorSrcFile':False,
    'outputMethodsBeforeAttributes': True,
    
    ## @@TR: The following really belong in the parser, but I've put them
    ## here for the time being to facilitate separating the parser and
    ## compiler:
    'cheetahVarStartToken':'$',
    'commentStartToken':'##',
    'multiLineCommentStartToken':'#*',
    'multiLineCommentEndToken':'*#',
    'directiveStartToken':'#',
    'directiveEndToken':'#',
    'PSPStartToken':'<%',
    'PSPEndToken':'%>',
    'EOLSlurpToken':'#',
    'gettextTokens': ["_", "N_", "ngettext"],
    'allowExpressionsInExtendsDirective': False,
    'allowEmptySingleLineMethods': False,
    'allowNestedDefScopes': True,
    'allowPlaceholderFilterArgs': True,
    
    # input filtering/restriction
    # use lower case keys here!!
    'disabledDirectives':[], # list of directive keys, without the start token
    'enabledDirectives':[], # list of directive keys, without the start token

    'disabledDirectiveHooks':[], # callable(parser, directiveKey)
    'preparseDirectiveHooks':[], # callable(parser, directiveKey)
    'postparseDirectiveHooks':[], # callable(parser, directiveKey)
    'preparsePlaceholderHooks':[], # callable(parser)
    'postparsePlaceholderHooks':[], # callable(parser)
    # the above hooks don't need to return anything

    'expressionFilterHooks':[], # callable(parser, expr, exprType, rawExpr=None, startPos=None)
    # exprType is the name of the directive, 'psp', or 'placeholder'. all
    # lowercase.  The filters *must* return the expr or raise an exception.
    # They can modify the expr if needed.


    'templateMetaclass':'TemplateMetaClass',
    }

#class ModuleCompiler(Parser, GenUtils):
class ModuleCompiler(SettingsManager, GenUtils):

    parserClass = Parser
    classCompilerClass = AutoClassCompiler
    
    def __init__(self, source=None, file=None, moduleName='GenTemplate',
                 mainClassName=None,
                 mainMethodName=None,
                 templateObj=None,
                 settings=None):
        SettingsManager.__init__(self)
        if settings:
            self.updateSettings(settings)
        # disable useStackFrames if the C version of NameMapper isn't compiled
        # it's painfully slow in the Python version and bites Windows users all
        # the time:
        if not NameMapper.C_VERSION:
            warnings.warn(
                "\nYou don't have the C version of NameMapper installed! "
                "I'm disabling Cheetah's useStackFrames option as it is "
                 "painfully slow with the Python version of NameMapper. "
                "You should get a copy of Cheetah with the compiled C version of NameMapper."
                )
            self.setSetting('useStackFrames', False)                    

        self._templateObj = templateObj
        self._compiled = False
        self._moduleName = moduleName
        if not mainClassName:
            self._mainClassName = moduleName
        else:
            self._mainClassName = mainClassName
        self._mainMethodNameArg = mainMethodName
        if mainMethodName:
            self.setSetting('mainMethodName', mainMethodName)
        
        self._filePath = None
        self._fileMtime = None
        
        if source and file:
            raise TypeError("Cannot compile from a source string AND file.")
        elif isinstance(file, types.StringType) or isinstance(file, types.UnicodeType): # it's a filename.

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

        if not (isinstance(source, str) or isinstance(source, unicode)):
            source = str( source )
        # by converting to string here we allow objects such as other Templates
        # to be passed in

        # Handle the #indent directive by converting it to other directives.
        # (Over the long term we'll make it a real directive.)
        if source == "":
            warnings.warn("You supplied an empty string for the source!", )
        
        if source.find('#indent') != -1: #@@TR: undocumented hack
            source = indentize(source)

        self._parser = self.parserClass(source, filename=self._filePath, compiler=self)
        self._setupCompilerState()
        
    def __getattr__(self, name):
        """Provide one-way access to the methods and attributes of the
        ClassCompiler, and thereby the MethodCompilers as well.

        WARNING: Use .setMethods to assign the attributes of the ClassCompiler
        from the methods of this class!!! or you will be assigning to attributes
        of this object instead.
        """
        
        if self.__dict__.has_key(name):
            return self.__dict__[name]
        elif hasattr(self.__class__, name):
            return getattr(self.__class__, name)
        elif self._activeClassesList and hasattr(self._activeClassesList[-1], name):
            return getattr(self._activeClassesList[-1], name)
        else:
            raise AttributeError, name


    def _initializeSettings(self):
        self.updateSettings( DEFAULT_COMPILER_SETTINGS.copy() )
        
    def _setupCompilerState(self):
        self._activeClassesList = []
        self._finishedClassesList = []      # listed by ordered 
        self._finishedClassIndex = {}  # listed by name
        
        self._moduleDef = None
        self._moduleShBang = '#!/usr/bin/env python'
        self._moduleEncoding = 'ascii'
        self._moduleEncodingStr = ''
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
            "import __builtin__",
            "from Cheetah.Template import Template",
            "from Cheetah.Template import TemplateMetaClass",
            "from Cheetah.DummyTransaction import DummyTransaction",
            "from Cheetah.NameMapper import NotFound, valueForName, valueFromSearchList, valueFromFrameOrSearchList",
            "from Cheetah.CacheRegion import CacheRegion",
            "import Cheetah.Filters as Filters",
            "import Cheetah.ErrorCatchers as ErrorCatchers",
            ]        

        self._importedVarNames = ['sys',
                                  'os',
                                  'os.path',
                                  'time',
                                  'types',
                                  'Template',
                                  'DummyTransaction',
                                  'NotFound',
                                  'Filters',
                                  'ErrorCatchers',
                                  'CacheRegion',
                                  ]
        
        self._moduleConstants = [
            "try:",
            "    True, False",
            "except NameError:",
            "    True, False = (1==1), (1==0)",
            "VFFSL=valueFromFrameOrSearchList",
            "VFSL=valueFromSearchList",
            "VFN=valueForName",
            "currentTime=time.time",
            ]
        
    def compile(self):
        classCompiler = self._spawnClassCompiler(self._mainClassName)            
        self._addActiveClassCompiler(classCompiler)
        self._parser.parse()
        self._swallowClassCompiler(self._popActiveClassCompiler())
        self._compiled = True

        
    def _spawnClassCompiler(self, className, klass=None):
        if klass is None:
            klass = self.classCompilerClass
        classCompiler = klass(className,
                              moduleCompiler=self,
                              mainMethodName=self.setting('mainMethodName'),
                              templateObj=self._templateObj,
                              fileName=self._filePath,
                              settingsManager=self,
                              )
        return classCompiler

    def _addActiveClassCompiler(self, classCompiler):
        self._activeClassesList.append(classCompiler)

    def _getActiveClassCompiler(self):
        return self._activeClassesList[-1]

    def _popActiveClassCompiler(self):
        return self._activeClassesList.pop()

    def _swallowClassCompiler(self, classCompiler):
        classCompiler.cleanupState()
        self._finishedClassesList.append( classCompiler )
        self._finishedClassIndex[classCompiler.className()] = classCompiler
        return classCompiler

    def _finishedClasses(self):
        return self._finishedClassesList


    def importedVarNames(self):
        return self._importedVarNames
    
    def addImportedVarNames(self, varNames):
        self._importedVarNames.extend(varNames)               
        
    ## methods for adding stuff to the module and class definitions

    def setBaseClass(self, baseClassName):
        if self._mainMethodNameArg:
            self.setMainMethodName(self._mainMethodNameArg)
        else:
            self.setMainMethodName(self.setting('mainMethodNameForSubclasses'))
       
        ##################################################
        ## If the #extends directive contains a classname or modulename that isn't
        #  in self.importedVarNames() already, we assume that we need to add
        #  an implied 'from ModName import ClassName' where ModName == ClassName.
        #  - This is the case in WebKit servlet modules.
        #  - We also assume that the final . separates the classname from the
        #    module name.  This might break if people do something really fancy 
        #    with their dots and namespaces.

        if (not self.setting('autoImportForExtendDirective')
            or baseClassName=='object' or baseClassName in self.importedVarNames()):
            self._getActiveClassCompiler().setBaseClass(baseClassName)
            # no need to import
        else:
            chunks = baseClassName.split('.')
            if len(chunks)==1:
                self._getActiveClassCompiler().setBaseClass(baseClassName)
                if baseClassName not in self.importedVarNames():
                    modName = baseClassName
                    # we assume the class name to be the module name
                    # and that it's not a builtin:
                    importStatement = "from %s import %s" % (modName, baseClassName)
                    self.addImportStatement(importStatement)
                    self.addImportedVarNames( [baseClassName,] ) 
            else:
                needToAddImport = True
                modName = chunks[0]
                #print chunks, ':', self.importedVarNames()
                for chunk in chunks[1:-1]:
                    if modName in self.importedVarNames():
                        needToAddImport = False
                        finalBaseClassName = baseClassName.replace(modName+'.', '')
                        self._getActiveClassCompiler().setBaseClass(finalBaseClassName)
                        break
                    else:
                        modName += '.'+chunk                        
                if needToAddImport:
                    modName, finalClassName = '.'.join(chunks[:-1]), chunks[-1]                
                    #if finalClassName != chunks[:-1][-1]:
                    if finalClassName != chunks[-2]:
                        # we assume the class name to be the module name
                        modName = '.'.join(chunks)
                    self._getActiveClassCompiler().setBaseClass(finalClassName)                        
                    importStatement = "from %s import %s" % (modName, finalClassName)
                    self.addImportStatement(importStatement)
                    self.addImportedVarNames( [finalClassName,] ) 

        
        ##################################################
        ## dynamically bind to and __init__ with this new baseclass
        #  - this is required for dynamic use of templates compiled directly from file
        #  - also necessary for the 'monitorSrc' fileMtime triggered recompiles
        
        if self._templateObj:
            mod = self._templateObj._importAsDummyModule('\n'.join(self._importStatements))
            baseClass = getattr(mod, self._baseClass, getattr(__builtin__,self._baseClass, None))
            assert baseClass
            class newClass(baseClass):pass            
            self._templateObj._assignRequiredMethodsToClass(newClass)
            newClass.__name__ = self._mainClassName
            self._templateObj.__class__ = newClass
            # must initialize it so instance attributes are accessible
            newClass.__init__(self._templateObj,
                              _globalSetVars=self._templateObj._CHEETAH_globalSetVars,
                              _preBuiltSearchList=self._templateObj._CHEETAH_searchList)

            if not hasattr(self._templateObj, 'transaction'):
                self._templateObj.transaction = None
            if (not hasattr(self._templateObj, 'respond')
                and self._mainMethodName==self.setting('mainMethodNameForSubclasses')):                
                self.setMainMethodName('respond')
            
    def setCompilerSetting(self, key, valueExpr):
        self.setSetting(key, eval(valueExpr) )
        self._parser.configureParser()

    def setCompilerSettings(self, keywords, settingsStr):
        KWs = keywords
        merge = True
        if 'nomerge' in KWs:
            merge = False
            
        if 'reset' in KWs:
            # @@TR: this is actually caught by the parser at the moment. 
            # subject to change in the future
            self._initializeSettings()
            self._parser.configureParser()
            return
        elif 'python' in KWs:
            settingsReader = self.updateSettingsFromPySrcStr
            # this comes from SettingsManager
        else:
            # this comes from SettingsManager
            settingsReader = self.updateSettingsFromConfigStr

        settingsReader(settingsStr)
        self._parser.configureParser()
        
    def setShBang(self, shBang):
        self._moduleShBang = shBang
    
    def setModuleEncoding(self, encoding):
        self._moduleEncoding = encoding
        self._moduleEncodingStr = '# -*- coding: %s -*-' %encoding

    def getModuleEncoding(self):
        return self._moduleEncoding

    def addModuleHeader(self, line):
        """Adds a header comment to the top of the generated module.
        """
        self._moduleHeaderLines.append(line)
        
    def addModuleDocString(self, line):        
        """Adds a line to the generated module docstring.
        """
        self._moduleDocStringLines.append(line)

    def addModuleGlobal(self, line):
        """Adds a line of global module code.  It is inserted after the import
        statements and Cheetah default module constants.
        """
        self._moduleConstants.append(line)
        if self._templateObj:
            mod = self._execInDummyModule(line)

    def addSpecialVar(self, basename, contents, includeUnderscores=True):
        """Adds module __specialConstant__ to the module globals.
        """
        name = includeUnderscores and '__'+basename+'__' or basename
        self._specialVars[name] = contents.strip()

    def _getDummyModuleForDynamicCompileHack(self):
        mod = self._templateObj._getDummyModuleForDynamicCompileHack()
        if mod not in self._templateObj._CHEETAH_searchList:
            # @@TR 2005-01-15: testing this approach to support
            # 'from foo import *'
            self._templateObj._CHEETAH_searchList.append(mod)
        return mod

    def _execInDummyModule(self, code):
        mod = self._getDummyModuleForDynamicCompileHack()        
        co = compile(code+'\n', mod.__file__, 'exec')
        exec co in mod.__dict__
        return mod

    def addImportStatement(self, impStatement):
        self._importStatements.append(impStatement)

        #@@TR 2005-01-01: there's almost certainly a cleaner way to do this!
        importVarNames = impStatement[impStatement.find('import') + len('import'):].split(',')
        importVarNames = [var.split()[-1] for var in importVarNames] # handles aliases
        importVarNames = [var for var in importVarNames if var!='*']
        self.addImportedVarNames(importVarNames) #used by #extend for auto-imports
        
        if self._templateObj:
            mod = self._execInDummyModule(impStatement)
            # @@TR: old buggy approach is still needed for now
            import Template as TemplateMod
            for varName in importVarNames: 
                if varName == '*': continue
                val = getattr(mod, varName.split('.')[0])
                setattr(TemplateMod, varName, val)

    def addAttribute(self, attribName, expr):
        self._getActiveClassCompiler().addAttribute(attribName + ' =' + expr)
        if self._templateObj:
            # @@TR: this code should be delegated to the compiler
            val = eval(expr,{},{})
            setattr(self._templateObj, attribName, val)
        
    def addComment(self, comm):
        if re.match(r'#+$',comm):      # skip bar comments
            return
        
        specialVarMatch = specialVarRE.match(comm)
        if specialVarMatch:
            # @@TR: this is a bit hackish and is being replaced with
            # #set module varName = ...
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
    
    def getModuleCode(self):
        if not self._compiled:
            self.compile()
        if self._moduleDef:
            return self._moduleDef
        else:
            return self.wrapModuleDef()
        
    __str__ = getModuleCode


    def wrapModuleDef(self):
        self.addSpecialVar('CHEETAH_docstring', self.setting('defDocStrMsg'))
        self.addSpecialVar('CHEETAH_version', Version)
        self.addSpecialVar('CHEETAH_genTime', self.timestamp())
        if self._filePath:
            timestamp = self.timestamp(self._fileMtime)
            self.addSpecialVar('CHEETAH_src', self._filePath)
            self.addSpecialVar('CHEETAH_srcLastModified', timestamp)
            
        moduleDef = """%(header)s
%(docstring)s

##################################################
## DEPENDENCIES
%(imports)s

##################################################
## MODULE CONSTANTS
%(constants)s
%(specialVars)s

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
        header += self._moduleEncodingStr + '\n'
        if self._moduleHeaderLines:
            offSet = self.setting('commentOffset')
        
            header += (
                '#' + ' '*offSet + 
                ('\n#'+ ' '*offSet).join(self._moduleHeaderLines) +
                '\n'
                )

        return header

    def moduleDocstring(self):
        if not self._moduleDocStringLines:
            return ''
        
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
        classDefs = [str(klass) for klass in self._finishedClasses() ]
        return '\n\n'.join(classDefs)

    def moduleFooter(self):
        return """
# CHEETAH was developed by Tavis Rudd and Mike Orr
# with code, advice and input from many other volunteers.
# For more information visit http://www.CheetahTemplate.org/

##################################################
## if run from command line:
if __name__ == '__main__':
    from Cheetah.TemplateCmdLineIface import CmdLineIface
    CmdLineIface(templateObj=%(className)s()).run()

""" % {'className':self._mainClassName}


##################################################
## Make Compiler an alias for ModuleCompiler
    
Compiler = ModuleCompiler


