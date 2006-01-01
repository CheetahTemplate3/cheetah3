#!/usr/bin/env python
# $Id: Compiler.py,v 1.98 2006/01/01 23:39:02 tavis_rudd Exp $
"""Compiler classes for Cheetah:
ModuleCompiler aka 'Compiler'
ClassCompiler
MethodCompiler

If you are trying to grok this code start with ModuleCompiler.__init__,
ModuleCompiler.compile, and ModuleCompiler.__getattr__.

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@damnsimple.com>
Version: $Revision: 1.98 $
Start Date: 2001/09/19
Last Revision Date: $Date: 2006/01/01 23:39:02 $
"""
__author__ = "Tavis Rudd <tavis@damnsimple.com>"
__revision__ = "$Revision: 1.98 $"[11:-2]

import sys
import os
import os.path
from os.path import getmtime, exists
import re
import types
import time
import random
import warnings

from Cheetah.Version import Version
from Cheetah.SettingsManager import SettingsManager
from Cheetah.Parser import Parser, ParseError, specialVarRE, STATIC_CACHE, REFRESH_CACHE
from Cheetah.Utils.Indenter import indentize # an undocumented preprocessor
from Cheetah import ErrorCatchers
from Cheetah import NameMapper

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
        (Unified Dotted Notation with the SearchList)."""
        
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
    def __init__(self, methodName, classCompiler, templateObj=None):
        self._settingsManager = classCompiler
        self._classCompiler = classCompiler
        self._templateObj = templateObj
        self._methodName = methodName
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
        self._callRegionOpen = False
        self._isErrorCatcherOn = False
        
    def cleanupState(self):
        """Called by the containing class compiler instance"""
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
        ind = self._indent*2
        
        docStr = (ind + '"""\n' + ind +
                  ('\n' + ind).join(self._docStringLines) +
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
        """
        """
        if filterArgs is None:
            filterArgs = ''
        if self.setting('includeRawExprInFilterArgs') and rawExpr:
            filterArgs += ', rawExpr=%s'%repr(rawExpr)

        if self.setting('alwaysFilterNone'):
            if rawExpr and rawExpr.find('\n')==-1 and rawExpr.find('\r')==-1:
                self.addChunk("__v = %s # <- %s"%(chunk, rawExpr))
            else:
                self.addChunk("__v = %s"%chunk)
                
            if self.setting('useFilters'):
                self.addChunk("if __v is not None: write(__filter(__v%s))"%filterArgs)
            else:
                self.addChunk("if __v is not None: write(str(__v))")
        else:
            
            if self.setting('useFilters'):
                self.addChunk("write(__filter(%s%s))"%(chunk,filterArgs))
            else:
                self.addChunk("write(str(%s))"%chunk)



    def _appendToPrevStrConst(self, strConst):
        if self._pendingStrConstChunks:
            self._pendingStrConstChunks.append(strConst)
        else:
            self._pendingStrConstChunks = [strConst]

    def _unescapeCheetahVars(self, theString):
        """Unescape any escaped Cheetah \$vars in the string."""
        
        token = self.setting('cheetahVarStartToken')
        return theString.replace('\\' + token, token)

    def _unescapeDirectives(self, theString):
        """Unescape any escaped Cheetah \$vars in the string."""
        
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

    def addVariablePlaceholder(self, varNameChunks,
                               restOfExpr,
                               filterArgs, rawPlaceholder, cacheTokenParts, lineCol):
        expr  = self.genCheetahVar(varNameChunks)
        if restOfExpr:
            expr = expr + ' ' + restOfExpr
        self._addPlaceholder(expr,
                             filterArgs=filterArgs,
                             rawPlaceholder=rawPlaceholder,
                             cacheTokenParts=cacheTokenParts,
                             lineCol=lineCol)        

    def addExpressionPlaceholder(self, expr, rawPlaceholder, cacheTokenParts, lineCol):
        self._addPlaceholder(expr,
                             filterArgs=None,
                             rawPlaceholder=rawPlaceholder,
                             cacheTokenParts=cacheTokenParts,
                             lineCol=lineCol)        

    def _addPlaceholder(self, expr, filterArgs, rawPlaceholder, cacheTokenParts, lineCol):
        cacheInfo = self.genCacheInfo(cacheTokenParts) 
        if cacheInfo:
            cacheInfo['ID'] = repr(rawPlaceholder)[1:-1]
            self.startCacheRegion(cacheInfo, lineCol)

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
        
    def addSet(self, LVALUE, OP, RVALUE, isGlobal=True):
        ## we need to split the LVALUE to deal with globalSetVars
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
            LVALUE = 'self._CHEETAH_globalSetVars["' + primary + '"]' + secondary            
        else:
            pass
        self.addChunk( LVALUE + ' ' + OP + ' ' + RVALUE.strip() )

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

    def addTry(self, expr):
        self.addIndentingDirective(expr)
        
    def addExcept(self, expr):
        self.addReIndentingDirective(expr)
        
    def addFinally(self, expr):
        self.addReIndentingDirective(expr)
            
    def addReturn(self, expr):
        self.addChunk(expr)

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
                self.addWriteChunk('__filter(' + PSP + ')')
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
        return str(random.randrange(100, 999)) \
               + str(random.randrange(10000, 99999))
        
    def startCacheRegion(self, cacheInfo, lineCol):
        ID = self.nextCacheID()
        interval = cacheInfo.get('interval',None)
        test = cacheInfo.get('test',None)
        
        customID = cacheInfo.get('id',None)
        if customID:
            ID = repr(customID)
        varyBy = cacheInfo.get('varyBy',ID)

        self._cacheRegionOpen = True    # attrib of current methodCompiler
        
        self.addChunk('## START CACHE REGION: at line, col ' + str(lineCol) + ' in the source.')
        self.addChunk('RECACHE = False')

        self.addChunk('region = self._CHEETAH_cacheRegions.get(' + ID + ')')
        
        self.addChunk('if not region:')
        self.indent()
        self.addChunk("region = CacheRegion()")
        self.addChunk("self._CHEETAH_cacheRegions[" + ID + "] = region")
        self.addChunk('RECACHE = True')
        self.dedent()
        
        self.addChunk('cache = region.getCache('+varyBy+')')

        if interval:
            self.addMethDocString('This cache will be refreshed every ' +
                                  str(interval) + ' seconds.')
            self.addChunk('if (not cache.getRefreshTime())' +
                          ' or (currentTime() > cache.getRefreshTime()):')
            self.indent()
            self.addChunk("cache.setRefreshTime(currentTime() +" + str(interval) + ")")
            self.addChunk('RECACHE = True')
            self.dedent()
            
        if test:
            self.addChunk('if ' + test + ':')
            self.indent()
            self.addChunk('RECACHE = True')
            self.dedent()
            
        self.addChunk('if RECACHE or not cache.getData():')
        self.indent()
        self.addChunk('orig_trans = trans')
        self.addChunk('trans = cacheCollector = DummyTransaction()')
        self.addChunk('write = cacheCollector.response().write')
        
    def endCacheRegion(self):
        self._cacheRegionOpen = False
        self.addChunk('trans = orig_trans')
        self.addChunk('write = trans.response().write')
        self.addChunk('cache.setData(cacheCollector.response().getvalue())')
        self.addChunk('del cacheCollector')
        
        self.dedent()        
        self.addWriteChunk('cache.getData()')
        self.addChunk('## END CACHE REGION')
        self.addChunk('')

    def startCallRegion(self, callSignature, lineCol):
        assert not self._callRegionOpen
        self._callRegionOpen = True    # attrib of current methodCompiler
        self._currentCallSignature = (callSignature, lineCol)
        self._currentCallUsesKeywordArgs = False
        self.addChunk('## START CALL REGION: '+callSignature
                      +' at line, col ' + str(lineCol) + ' in the source.')
        self.addChunk('__orig_trans = trans')
        self.addChunk('trans = __callCollector = DummyTransaction()')
        self.addChunk('write = __callCollector.response().write')

    def setCallArg(self, argName, lineCol):
        assert self._callRegionOpen
        if self._currentCallUsesKeywordArgs:
            self._endCallArg()
        else:
            self._currentCallUsesKeywordArgs = True
            self.addChunk('__callKws = {}')
            self.addChunk('__currentCallArgname = %r'%argName)
        self._currentCallArgname = argName
        
    def _endCallArg(self):
        self.addChunk(
            '__callKws[%r] = __callCollector.response().getvalue()'%
            self._currentCallArgname)
        self.addChunk('del __callCollector')
        self.addChunk('trans = __callCollector = DummyTransaction()')
        self.addChunk('write = __callCollector.response().write')
    
    def endCallRegion(self):
        assert self._callRegionOpen
        callSignature, lineCol = self._currentCallSignature
        self._callRegionOpen = False    # attrib of current methodCompiler
        self._currentCallSignature = None
        self.addChunk('trans = __orig_trans')
        self.addChunk('write = trans.response().write')
        if not self._currentCallUsesKeywordArgs:
            self.addChunk('__callArgVal = __callCollector.response().getvalue()')
            self.addChunk('del __callCollector')
            self.addFilteredChunk('%s(__callArgVal)'%callSignature)
            self.addChunk('del __callArgVal')
        else:
            self._endCallArg()
            self.addFilteredChunk('%s(**__callKws)'%callSignature)
            self.addChunk('del __callKws')
        self.addChunk('## END CALL REGION: '+callSignature
                      +' at line, col ' + str(lineCol) + ' in the source.')        
        self.addChunk('')
    
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
            self.addChunk('__filter = self._CHEETAH_currentFilter = ' + theFilter.strip() +
                          '(self).filter')
        else:
            if theFilter.lower() == 'none':
                self.addChunk('__filter = self._CHEETAH_initialFilter')
            else:
                # is string representing the name of a builtin filter
                self.addChunk('filterName = ' + repr(theFilter))
                self.addChunk('if self._CHEETAH_filters.has_key("' + theFilter + '"):')
                self.indent()
                self.addChunk('__filter = self._CHEETAH_currentFilter = self._CHEETAH_filters[filterName]')
                self.dedent()
                self.addChunk('else:')
                self.indent()
                self.addChunk('__filter = self._CHEETAH_currentFilter = \\\n\t\t\tself._CHEETAH_filters[filterName] = '
                              + 'getattr(self._CHEETAH_filtersLib, filterName)(self).filter')
                self.dedent()
                
    def closeFilterBlock(self):
        self.addChunk('__filter = self._CHEETAH_initialFilter')        

class AutoMethodCompiler(MethodCompiler):

    def _setupState(self):
        MethodCompiler._setupState(self)
        self._argStringList = [ ("self",None) ]
        self._streamingEnabled = True
        
    def cleanupState(self):
        MethodCompiler.cleanupState(self)
        self.commitStrConst()
        if self._cacheRegionOpen:
            self.endCacheRegion()
        if self._callRegionOpen:
            self.endCallRegion()
            
        self._indentLev = self.setting('initialMethIndentLevel')
        mainBodyChunks = self._methodBodyChunks
        self._methodBodyChunks = []
        self._addAutoSetupCode()
        self._methodBodyChunks.extend(mainBodyChunks)
        self._addAutoCleanupCode()
        if self._streamingEnabled:
            argList = [ ('trans', 'None'),
                        #("__dummyTrans","False"),
                        ]
            if self.setting('useNameMapper'):
                argList.extend([("VFFSL","valueFromFrameOrSearchList"), 
                                ("VFN","valueForName")])
            for argName, defVal in  argList:
                self.addMethArg(argName, defVal)
        
    def _addAutoSetupCode(self):
        if self._streamingEnabled:
            self.addChunk('if not trans and not callable(self.transaction): trans = self.transaction'
                          ' # is None unless self.awake() was called')
            self.addChunk('if not trans:')
            self.indent()
            self.addChunk('trans = DummyTransaction()')
            if self.setting('autoAssignDummyTransactionToSelf'):
                self.addChunk('self.transaction = trans')            
            self.addChunk('__dummyTrans = True')
            self.dedent()
            self.addChunk('else: __dummyTrans = False')

        else:
            self.addChunk('trans = DummyTransaction()')
            self.addChunk('__dummyTrans = True')
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
            self.addChunk('__filter = self._CHEETAH_currentFilter')
        self.addChunk('')

        self.addChunk("#" *40)
        self.addChunk('## START - generated method body')
        self.addChunk('')

    def _addAutoCleanupCode(self):
        self.addChunk('')
        self.addChunk("#" *40)
        self.addChunk('## END - generated method body')
        self.addChunk('')
        self.addStop()
        self.addChunk('')
        
    def addStop(self, expr=None):
        self.addChunk('return __dummyTrans and trans.response().getvalue() or ""')

    def addMethArg(self, name, defVal=None):
        asteriskPos = max(name.rfind('*')+1, 0)
        if asteriskPos:
            self._streamingEnabled = False
        self._argStringList.append( (name,defVal) )
        
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

_initMethod_setupArbitraryClass = """\
if not self._CHEETAH_instanceInitialized:
    if not hasattr(self, '_initCheetahAttributes'):
        templateClass = getattr(self, '_CHEETAH_templateClass', Template)
        #templateClass.assignRequiredMethodsToClass(self.__class__)
        templateClass.assignRequiredMethodsToClass(%(className)s)
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
                 templateObj=None,
                 fileName=None,
                 settingsManager=None):

        self._settingsManager = settingsManager
        self._fileName = fileName
        self._className = className
        self._mainMethodName = mainMethodName
        self._templateObj = templateObj
        self._setupState()
        methodCompiler = self._spawnMethodCompiler(mainMethodName)
        methodCompiler.addMethDocString('This is the main method generated by Cheetah')
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
        __init__.addChunk(_initMethod_setupArbitraryClass%dict(className=self._className))
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
        
    
    def _spawnMethodCompiler(self, methodName, klass=None):
        if klass is None:
            klass = self.methodCompilerClass
        methodCompiler = klass(methodName, classCompiler=self, templateObj=self._templateObj)
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
        methodCompiler = self._spawnMethodCompiler(methodName)
        self._setActiveMethodCompiler(methodCompiler)
        
        ## deal with the method's argstring
        for argName, defVal in argsList:
            methodCompiler.addMethArg(argName, defVal)

        methodCompiler.addMethDocString(parserComment)            
        
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
        
        catcherMeth = self._spawnMethodCompiler(methodName, klass=MethodCompiler)
        catcherMeth.setMethodSignature('def ' + methodName +
                                       '(self, localsDict={})')
                                        # is this use of localsDict right?
        catcherMeth.addMethDocString('Generated from ' + rawCode +
                                   ' at line, col ' + str(lineCol) + '.') 
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
    'useFilterArgsInPlaceholders':True,
    'includeRawExprInFilterArgs':True,
    
    #'lookForTransactionAttr':False,
    'autoAssignDummyTransactionToSelf':False,
    
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
    
    # input filtering/restriction
    # use lower case keys here!!
    'disabledDirectives':[], # list of directive keys, without the start token
    'enabledDirectives':[], # list of directive keys, without the start token

    'disabledDirectiveHooks':[], # callable(parser, directiveKey)
    'preparseDirectiveHooks':[], # callable(parser, directiveKey)
    'postparseDirectiveHooks':[], # callable(parser, directiveKey)
    'preparsePlaceholderHooks':[], # callable(parser)
    'postparsePlaceholderHooks':[], # callable(parser)
    'expressionFilterHooks':[], # callable(parser, expr, exprType, rawExpr=None, startPos=None)
    # exprType is the name of the directive, 'psp', or 'placeholder'. all lowercase
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
        of this object instead."""
        
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
        self._moduleEncoding = ''
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
            class newClass:
                pass
            newClass.__name__ = self._mainClassName
            __bases__ = (getattr(mod, self._baseClass), )
            newClass.__bases__ = __bases__
            self._templateObj.__class__ = newClass
            # must initialize it so instance attributes are accessible
            newClass.__init__(self._templateObj,
                              _globalSetVars=self._templateObj._CHEETAH_globalSetVars,
                              _preBuiltSearchList=self._templateObj._CHEETAH_searchList)

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
        self._moduleEncoding = '# -*- coding: %s -*-' %encoding

    def addModuleHeader(self, line):
        self._moduleHeaderLines.append(line)
        
    def addModuleDocString(self, line):        
        self._moduleDocStringLines.append(line)

    def addSpecialVar(self, basename, contents):
        self._specialVars['__' + basename + '__'] = contents.strip()

    def addImportStatement(self, impStatement):
        self._importStatements.append(impStatement)

        #@@TR 2005-01-01: there's almost certainly a cleaner way to do this!
        importVarNames = impStatement[impStatement.find('import') + len('import'):].split(',')
        importVarNames = [var.split()[-1] for var in importVarNames] # handles aliases
        importVarNames = [var for var in importVarNames if var!='*']
        self.addImportedVarNames(importVarNames) #used by #extend for auto-imports
        
        if self._templateObj:
            import Template as TemplateMod
            mod = self._templateObj._importAsDummyModule(impStatement)

            # @@TR 2005-01-15: testing this approach to support
            # 'from foo import *'
            self._templateObj._CHEETAH_searchList.append(mod)

            # @@TR: old buggy approach is still needed for now
            for varName in importVarNames: 
                if varName == '*': continue
                val = getattr(mod, varName.split('.')[0])
                setattr(TemplateMod, varName, val)

    def addGlobalCodeChunk(self, codeChunk):
        self._globalCodeChunks.append(codeChunk)


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
        header += self._moduleEncoding + '\n'
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
        classDefs = [str(klass) for klass in self._finishedClasses() ]
        return '\n\n'.join(classDefs)

    def moduleFooter(self):
        return """
# CHEETAH was developed by Tavis Rudd and Mike Orr
# with code, advice and input from many other volunteers.
# For more information visit http://www.CheetahTemplate.org

##################################################
## if run from command line:
if __name__ == '__main__':
    from Cheetah.TemplateCmdLineIface import CmdLineIface
    CmdLineIface(templateObj=%(className)s()).run()

""" % {'className':self._mainClassName}


##################################################
## Make Compiler an alias for ModuleCompiler
    
Compiler = ModuleCompiler


