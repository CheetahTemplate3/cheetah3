#!/usr/bin/env python
# $Id: Parser.py,v 1.39 2002/01/23 20:20:20 tavis_rudd Exp $
"""Parser classes for Cheetah's Compiler

Classes:
  ParseError( Exception )
  _LowLevelSemanticsParser( Lexer )
  _HighLevelSemanticsParser( _LowLevelSemanticsParser )
  Parser === _HighLevelSemanticsParser (an alias)

where:
  Lexer ===  Cheetah.Lexer.Lexer(
                                 Cheetah.SettingsManager.SettingsManager,
                                 Cheetah.SourceReader.SourceReader
                                )

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
Version: $Revision: 1.39 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2002/01/23 20:20:20 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__revision__ = "$Revision: 1.39 $"[11:-2]

##################################################
## DEPENDENCIES ##
import os
import sys
import re
from re import DOTALL, MULTILINE
from types import StringType, ListType, TupleType

# intra-package imports ...
from Lexer import Lexer
import Filters
import ErrorCatchers
##################################################
## FUNCTIONS ##

# re tools
def escapeRegexChars(txt,
                     escapeRE=re.compile(r'([\$\^\*\+\.\?\{\}\[\]\(\)\|\\])')):
    
    """Return a txt with all special regular expressions chars escaped."""
    
    return escapeRE.sub(r'\\\1' , txt)

def group(*choices): return '(' + '|'.join(choices) + ')'
def nongroup(*choices): return '(?:' + '|'.join(choices) + ')'
def namedGroup(name, *choices): return '(P:<' + name +'>' + '|'.join(choices) + ')'
def any(*choices): return apply(group, choices) + '*'
def maybe(*choices): return apply(group, choices) + '?'

##################################################
## CONSTANTS & GLOBALS ##

True = (1==1)
False = (0==1)

NO_CACHE = 0
STATIC_CACHE = 1
REFRESH_CACHE = 2

##################################################
## Tokens for the parser ##

#generic
identchars = "abcdefghijklmnopqrstuvwxyz" \
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ_"
namechars = identchars + "0123456789"

#operators
powerOp = '**'
unaryArithOps = ('+', '-', '~')
binaryArithOps = ('+', '-', '/', '//','%')
shiftOps = ('>>','<<')
bitwiseOps = ('&','|','^')
assignOp = '='
augAssignOps = ('+=','-=','/=','*=', '**=','^=','%=',
          '>>=','<<=','&=','|=', )
assignmentOps = (assignOp,) + augAssignOps

compOps = ('<','>','==','!=','<=','>=', '<>', 'is', 'in',)
booleanOps = ('and','or','not')
operators = (powerOp,) + unaryArithOps + binaryArithOps \
            + shiftOps + bitwiseOps + assignmentOps \
            + compOps + booleanOps

delimeters = ('(',')','{','}','[',']',
              ',','.',':',';','=','`') + augAssignOps


keywords = ('and',       'del',       'for',       'is',        'raise',    
            'assert',    'elif',      'from',      'lambda',    'return',   
            'break',     'else',      'global',    'not',       'try',      
            'class',     'except',    'if',        'or',        'while',    
            'continue',  'exec',      'import',    'pass',
            'def',       'finally',   'in',        'print',
            )

single3 = "'''"
double3 = '"""'

tripleQuotedStringStarts =  ("'''", '"""', 
                             "r'''", 'r"""', "R'''", 'R"""',
                             "u'''", 'u"""', "U'''", 'U"""',
                             "ur'''", 'ur"""', "Ur'''", 'Ur"""',
                             "uR'''", 'uR"""', "UR'''", 'UR"""')

tripleQuotedStringPairs = {"'''": single3, '"""': double3,
                        "r'''": single3, 'r"""': double3,
                        "u'''": single3, 'u"""': double3,
                        "ur'''": single3, 'ur"""': double3,
                        "R'''": single3, 'R"""': double3,
                        "U'''": single3, 'U"""': double3,
                        "uR'''": single3, 'uR"""': double3,
                        "Ur'''": single3, 'Ur"""': double3,
                        "UR'''": single3, 'UR"""': double3,
                        }

closurePairs= {')':'(',']':'[','}':'{'}
closurePairsRev= {'(':')','[':']','{':'}'}

##################################################
## Regex chunks for the parser ##

tripleQuotedStringREs = {}
def makeTripleQuoteRe(start, end):
    start = escapeRegexChars(start)
    end = escapeRegexChars(end)
    return re.compile(r'(?:' + start + r').*?' + r'(?:' + end + r')', re.DOTALL)

for start, end in tripleQuotedStringPairs.items():
    tripleQuotedStringREs[start] = makeTripleQuoteRe(start, end)

WS = r'[ \f\t]*'  
EOL = r'\r\n|\n|\r'
EOLZ = EOL + r'|\Z'
escCharLookBehind = nongroup(r'(?<=\A)',r'(?<!\\)')
nameCharLookAhead = r'(?=[A-Za-z_])'


specialVarRE=re.compile(r'([a-zA-z_]+)@') # for matching specialVar comments
EOLre=re.compile(r'(?:\r\n|\r|\n)')

# e.g. ##author@ Tavis Rudd

##################################################
## CLASSES ##

class ParseError(ValueError):
    def __init__(self, stream, msg='Invalid Syntax', extMsg=''):
        self.stream = stream
        if stream.pos() >= len(stream):
            stream.setPos(len(stream) -1)
        self.msg = msg
        self.extMsg = extMsg
        
    def __str__(self):
        return self.report()

    def report(self):
        stream = self.stream
        if stream.filename():
            f = " in file %s" % stream.filename()
        else:
            f = ''
        report = ''
        row, col, line = self.stream.getRowColLine()


        ## get the surrounding lines
        lines = stream.splitlines()
        prevLines = []                  # (rowNum, content)
        for i in range(1,4):
            if row-1-i <=0:
                break
            prevLines.append( (row-i,lines[row-1-i]) )

        nextLines = []                  # (rowNum, content)
        for i in range(1,4):
            if not row-1+i < len(lines):
                break
            nextLines.append( (row+i,lines[row-1+i]) )
        nextLines.reverse()
        
        ## print the main message
        report += "\n\n%s at line %i, column %i%s\n\n" % (self.msg, row, col, f)
        report += 'Line|Line contents\n'
        report += '----|-------------------------------------------------------------\n'
        while prevLines:
            lineInfo = prevLines.pop()
            report += "%(row)-4d|%(line)s\n"% {'row':lineInfo[0], 'line':lineInfo[1]}
        report += "%(row)-4d|%(line)s\n"% {'row':row, 'line':line}
        report += ' '*5 +' '*(col-1) + "^\n"
        
        while nextLines:
            lineInfo = nextLines.pop()
            report += "%(row)-4d|%(line)s\n"% {'row':lineInfo[0], 'line':lineInfo[1]}
        ## add the extra msg
        if self.extMsg:
            report += self.extMsg + '\n'
            
        return report


class ArgList:

    """Used by _LowLevelSemanticsParser.getArgList()"""

    def __init__(self):
        self.argNames = []
        self.defVals = []
        self.i = 0

    def addArgName(self, name):
        self.argNames.append( name )
        self.defVals.append( None )

    def next(self):
        self.i += 1

    def addToDefVal(self, token):
        i = self.i
        if self.defVals[i] == None:
            self.defVals[i] = ''
        self.defVals[i] += token
    
    def merge(self):
        defVals = self.defVals
        for i in range(len(defVals)):
            if type(defVals[i]) == StringType:
                defVals[i] = defVals[i].strip()
                
        return map(None, [i.strip() for i in self.argNames], defVals)
    
    def __str__(self):
        return str(self.merge())
    
class _LowLevelSemanticsParser(Lexer):

    def _initializeSettings(self):
        defaults = {
            'cheetahVarStartToken':'$',
            
            #'placeholderStartToken':'$',   
            #'placeholderEndToken':None,
            # These will be used when placeholder parsing is separated from cheetahVar parsing
            
            'commentStartToken':'##',
            'multiLineCommentStartToken':'#*',
            'multiLineCommentEndToken':'*#',
            
            'directiveStartToken':'#',
            'directiveEndToken':'#',
            'PSPStartToken':'<%',
            'PSPEndToken':'%>',
            }
        if not hasattr(self, '_settings'):
            self._settings = defaults
        else:
            self.updateSettings(defaults)

    def configureParser(self):
        self.makeCheetahVarREs()
        self.makeCommentREs()
        self.makeDirectiveREs()
        self.makePspREs()
        self._possibleNonStrConstantChars = (
            self.setting('commentStartToken')[0] +
            self.setting('multiLineCommentStartToken')[0] + 
            self.setting('cheetahVarStartToken')[0] +
            self.setting('directiveStartToken')[0] +
            self.setting('PSPStartToken')[0])
        self._nonStrConstMatchers = [
            self.matchCommentStartToken,
            self.matchMultiLineCommentStartToken,
            self.matchCheetahVarStart,
            self.isDirective,
            self.matchPSPStartToken
            ]

    ## regex setup ##

    def makeCheetahVarREs(self):
        
        """Setup the regexs for Cheetah $var parsing."""

        num = r'[0-9\.]+'
        interval =   (r'(?P<interval>' + 
                      num + r's|' +
                      num + r'm|' +
                      num + r'h|' +
                      num + r'd|' +
                      num + r'w|' +
                      num + ')' 
                      )
    
        cacheToken = (r'(?:' +
                      r'(?P<REFRESH_CACHE>\*' + interval + '\*)'+
                      '|' +
                      r'(?P<STATIC_CACHE>\*)' +
                      '|' +
                      r'(?P<NO_CACHE>)' +
                      ')')
        self.cacheTokenRE = re.compile(cacheToken)
        
        self.cheetahVarStartRE = re.compile(
            escCharLookBehind +
            r'(?P<startToken>' +
            escapeRegexChars(self.setting('cheetahVarStartToken')) +
            ')' +
            r'(?P<cacheToken>' +
            cacheToken +
            ')' +
            r'(?P<enclosure>(?:|\{|\(|\[|)[ \t\f]*)' + # allow WS after enclosure
            r'(?=[A-Za-z_])')
        validCharsLookAhead = r'(?=[A-Za-z_\*!\{\(\[])'
        self.cheetahVarStartToken = self.setting('cheetahVarStartToken')
        self.cheetahVarStartTokenRE = re.compile(
            escCharLookBehind +
            escapeRegexChars(self.setting('cheetahVarStartToken')) +
            validCharsLookAhead)

    def makeCommentREs(self):
        """Construct the regex bits that are used in comment parsing."""
        
        startTokenEsc = escapeRegexChars(self.setting('commentStartToken'))
        self.commentStartTokenRE = re.compile(escCharLookBehind + startTokenEsc)
        del startTokenEsc
        
        startTokenEsc = escapeRegexChars(
            self.setting('multiLineCommentStartToken'))
        endTokenEsc = escapeRegexChars(
            self.setting('multiLineCommentEndToken'))
        self.multiLineCommentTokenStartRE = re.compile(escCharLookBehind +
                                                       startTokenEsc)
        self.multiLineCommentEndTokenRE = re.compile(escCharLookBehind +
                                                     endTokenEsc)
        
    def makeDirectiveREs(self):
        
        """Construct the regexs that are used in directive parsing."""
        
        startToken = self.setting('directiveStartToken')
        endToken = self.setting('directiveEndToken')
        startTokenEsc = escapeRegexChars(startToken)
        endTokenEsc = escapeRegexChars(endToken)
        
        validSecondCharsLookAhead = r'(?=[A-Za-z_])'
        self.directiveStartTokenRE = re.compile(escCharLookBehind + startTokenEsc
                                                + validSecondCharsLookAhead)
        self.directiveEndTokenRE = re.compile(escCharLookBehind + endTokenEsc)

    def makePspREs(self):
        
        """Setup the regexs for PSP parsing."""
        
        startToken = self.setting('PSPStartToken')
        startTokenEsc = escapeRegexChars(startToken)
        self.PSPStartTokenRE = re.compile(escCharLookBehind + startTokenEsc)
        
        endToken = self.setting('PSPEndToken')
        endTokenEsc = escapeRegexChars(endToken)
        self.PSPEndTokenRE = re.compile(escCharLookBehind + endTokenEsc)

        
    ## generic parsing methods ##
    #  - the gen* methods and add* methods are implemented by subclasses.

    def matchNonStrConst(self):
        if self.peek() in self._possibleNonStrConstantChars:
            for matcher in self._nonStrConstMatchers:
                if matcher():
                    return True
        return False

    def matchCommentStartToken(self):
        return self.commentStartTokenRE.match(self.src(), self.pos())
    
    def getCommentStartToken(self):
        match = self.matchCommentStartToken()
        if not match:
            raise ParseError(self, msg='Invalid single-line comment start token')
        return self.readTo(match.end())

    def matchMultiLineCommentStartToken(self):
        return self.multiLineCommentTokenStartRE.match(self.src(), self.pos())
    
    def getMultiLineCommentStartToken(self):
        match = self.matchMultiLineCommentStartToken()
        if not match:
            raise ParseError(self, msg='Invalid multi-line comment start token')
        return self.readTo(match.end())

    def matchMultiLineCommentEndToken(self):
        return self.multiLineCommentEndTokenRE.match(self.src(), self.pos())
    
    def getMultiLineCommentEndToken(self):
        match = self.matchMultiLineCommentEndToken()
        if not match:
            raise ParseError(self, msg='Invalid multi-line comment end token')
        return self.readTo(match.end())

    def lineClearToStartToken(self, pos=None):
        if pos == None:
            pos = self.pos()
        self.checkPos(pos)            
        src = self.src()
        BOL = self.findBOL()
        return BOL == pos or src[BOL:pos].isspace()

    def readToThisEndDirective(self, directiveKey):
        finalPos = endRawPos = startPos = self.pos()
        directiveChar = self.setting('directiveStartToken')[0]
        lineClearToStartToken = False
        while not self.atEnd():
            if self.peek() == directiveChar:
                if self.isDirective() == 'end':
                    endRawPos = self.pos()
                    self.getDirectiveStartToken()
                    self.advance(3)                 # to end of 'end'
                    self.getWhiteSpace()
                    if self.startswith(directiveKey):
                        if self.lineClearToStartToken(endRawPos):
                            lineClearToStartToken = True
                            endRawPos = self.findBOL(endRawPos)
                        self.advance(len(directiveKey)) # to end of directiveKey
                        self.getWhiteSpace()
                        finalPos = self.pos()
                        break
            self.advance()
            finalPos = endRawPos = self.pos()

        theBlock = self.readTo(endRawPos, start=startPos)
        self.setPos(finalPos)
        
        endOfFirstLinePos = self.findEOL()
        
        if self.matchDirectiveEndToken():
            self.getDirectiveEndToken()
        elif lineClearToStartToken and (not self.atEnd()) and self.peek() in '\r\n':
            self.readToEOL(gobble=True)
            
        if lineClearToStartToken and self.pos() > endOfFirstLinePos:
            self.delLeadingWS()
        return theBlock

    def matchWhiteSpace(self, WSchars=' \f\t'):
        return (not self.atEnd()) and  self.peek() in WSchars

    def getWhiteSpace(self, WSchars=' \f\t'):
        if not self.matchWhiteSpace(WSchars):
            return ''
        start = self.pos()
        while self.pos() < self._breakPoint:
            self.advance()
            if not self.matchWhiteSpace(WSchars):
                break
        return self._src[start:self.pos()]

    def matchNonWhiteSpace(self, WSchars=' \f\t\n\r'):
        return self.atEnd() or not self.peek() in WSchars

    def getNonWhiteSpace(self, WSchars=' \f\t\n\r'):
        if not self.matchNonWhiteSpace(WSchars):
            return ''
        start = self.pos()
        while self.pos() < self._breakPoint:
            self.advance()
            if not self.matchNonWhiteSpace(WSchars):
                break
        return self._src[start:self.pos()]
    
    def getDottedName(self):
        srcLen = len(self)
        nameChunks = []
        
        if not self.peek() in identchars:
            raise ParseError(self)
    
        while self.pos() < srcLen:
            c = self.peek()
            if c in namechars:
                nameChunk = self.getIdentifier()
                nameChunks.append(nameChunk)
            elif c == '.':
                if self.pos()+1 <srcLen and self.peek(1) in identchars:
                    nameChunks.append(self.getc())
                else:
                    break
            else:
                break

        return ''.join(nameChunks)

    def matchIdentifier(self,
                     identRE=re.compile(r'[a-zA-Z_][a-zA-Z_0-9]*')):
        return identRE.match(self.src(), self.pos())
    
    def getIdentifier(self):
        match = self.matchIdentifier()
        if not match:
            raise ParseError(self, msg='Invalid identifier')
        return self.readTo(match.end())

    def matchOperator(self):
        match = self.matchPyToken()
        if match and match.group() not in operators:
            match = None
        return match

    def getOperator(self):
        match = self.matchOperator()
        if not match:
            raise ParseError(self, msg='Expected operator')
        return self.readTo( match.end() )

    def matchAssignmentOperator(self):
        match = self.matchPyToken()
        if match and match.group() not in assignmentOps:
            match = None
        return match
        
    def getAssignmentOperator(self):
        match = self.matchAssignmentOperator()
        if not match:
            raise ParseError(self, msg='Expected assignment operator')
        return self.readTo( match.end() )

    def isDirective(self, directiveKeyChars=identchars+'-'):
        startPos = self.pos()
        if not self.matchDirectiveStartToken():
            return False

        self.getDirectiveStartToken()
        directiveKey = ''
        while self.pos() < self._breakPoint:
            c = self.getc()
            if not c in directiveKeyChars:
                break
            directiveKey += c
            
        if not directiveKey in self.directiveEaters.keys():
            directiveKey= False
        self.setPos(startPos)
                                        # DEBUG: print directiveKey, self.src()
        return directiveKey        
            
    def matchDirectiveStartToken(self):
        return self.directiveStartTokenRE.match(self.src(), self.pos())
    
    def getDirectiveStartToken(self):
        match = self.matchDirectiveStartToken()
        if not match:
            raise ParseError(self, msg='Invalid directive start token')
        return self.readTo(match.end())

    def matchDirectiveEndToken(self):
        return self.directiveEndTokenRE.match(self.src(), self.pos())
    
    def getDirectiveEndToken(self):
        match = self.matchDirectiveEndToken()
        if not match:
            raise ParseError(self, msg='Invalid directive end token')
        return self.readTo(match.end())

    def matchPSPStartToken(self):
        return self.PSPStartTokenRE.match(self.src(), self.pos())

    def matchPSPEndToken(self):
        return self.PSPEndTokenRE.match(self.src(), self.pos())

    def getPSPStartToken(self):
        match = self.matchPSPStartToken()
        if not match:
            raise ParseError(self, msg='Invalid psp start token')
        return self.readTo(match.end())

    def getPSPEndToken(self):
        match = self.matchPSPEndToken()
        if not match:
            raise ParseError(self, msg='Invalid psp end token')
        return self.readTo(match.end())

    def matchCheetahVarStart(self):
        """includes the enclosure and cache token"""
        return self.cheetahVarStartRE.match(self.src(), self.pos())
        
    def getCheetahVarStartToken(self):
        """just the start token, not the enclosure or cache token"""
        match = self.matchCheetahVarStart()
        if not match:
            raise ParseError(self, msg='Expected Cheetah $var start token')            
        return self.readTo( match.end('startToken') )

    def getCacheToken(self):
        try:
            token = self.cacheTokenRE.match(self.src(), self.pos())
            self.setPos( token.end() )
            return token.group()
        except:
            raise ParseError(self, msg='Expected cache token')


    def getTargetVarsList(self):
        varnames = []
        while not self.atEnd():
            if self.peek() in ' \t\f':
                self.getWhiteSpace()
            elif self.peek() in '\r\n':
                break
            elif self.startswith(','):
                self.advance()
            elif self.startswith('in ') or self.startswith('in\t'):
                break
            elif self.matchCheetahVarStart():
                self.getCheetahVarStartToken()
                self.getCacheToken()
                varnames.append( self.getDottedName() )
            elif self.matchIdentifier():
                varnames.append( self.getDottedName() )
            else:
                break
        return varnames
        
    def getCheetahVar(self, plain=False):
        """discards the cache info"""
        self.getCheetahVarStartToken()           
        self.getCacheToken()
        return self.getCheetahVarBody(plain=plain)
            
    def getCheetahVarBody(self, plain=False):
        return self.genCheetahVar(self.getCheetahVarNameChunks(), plain=plain)
        
    def getCheetahVarNameChunks(self):
        
        """
        nameChunks = list of Cheetah $var subcomponents represented as tuples
          [ (namemapperPart,autoCall,restOfName),
          ]
        where:
          namemapperPart = the dottedName base
          autocall = where NameMapper should use autocalling on namemapperPart
          restOfName = any arglist, index, or slice

        If restOfName contains a call arglist (e.g. '(1234)') then autocall is
        False, otherwise it defaults to True.

        EXAMPLE
        ------------------------------------------------------------------------

        if the raw CheetahVar is
          $a.b.c[1].d().x.y.z
          
        nameChunks is the list
          [ ('a.b.c',1,'[1]'),
            ('d',0,'()'),     
            ('x.y.z',1,''),   
          ]

        """
        
        chunks = []
        while self.pos() < len(self):
            rest = ''
            autoCall = True
            if not self.peek() in identchars + '.':
                break
            elif self.peek() == '.':
                
                if self.pos()+1 < len(self) and self.peek(1) in identchars:
                    self.advance()  # discard the period as it isn't needed with NameMapper
                else:
                    break
                
            dottedName = self.getDottedName()
            if not self.atEnd() and self.peek() in '([':
                if self.peek() == '(':
                    rest = self.getCallArgString()
                else:
                    rest = self.getExpression(enclosed=True)
                
                period = max(dottedName.rfind('.'), 0)
                if period:
                    chunks.append( (dottedName[:period], autoCall, '') )
                    dottedName = dottedName[period+1:]
                if rest and rest[0]=='(':
                    autoCall = False
            chunks.append( (dottedName, autoCall, rest) )

        return chunks
    

    def getCallArgString(self,
                         enclosures=[],  # list of tuples (char, pos), where char is ({ or [ 
                         ):

        """ Get a method/function call argument string. 

        This method understands *arg, and **kw
        """
        
        if enclosures:
            pass
        else:
            if not self.peek() == '(':
                raise ParseError(self, msg="Expected '('")
            startPos = self.pos()
            self.getc()
            enclosures = [('(', startPos),
                          ]
        
        argStringBits = ['(']
        addBit = argStringBits.append

        while 1:
            if self.atEnd():
                open = enclosures[-1][0]
                close = closurePairsRev[open]
                self.setPos(enclosures[-1][1])
                raise ParseError(
                    self, msg="EOF was reached before a matching '" + close +
                    "' was found for the '" + open + "'")

            c = self.peek()
            if c in ")}]": # get the ending enclosure and break                
                if not enclosures:
                    raise ParseError(self)
                c = self.getc()
                open = closurePairs[c]
                if enclosures[-1][0] == open:
                    enclosures.pop()
                    addBit(')')  
                    break
                else:
                    raise ParseError(self)
            elif c in " \t\f\r\n":
                addBit(self.getc())
            elif self.matchCheetahVarStart():
                startPos = self.pos()
                codeFor1stToken = self.getCheetahVar()
                WS = self.getWhiteSpace()
                if not self.atEnd() and self.peek() == '=':
                    nextToken = self.getPyToken()
                    if nextToken == '=':
                        endPos = self.pos()
                        self.setPos(startPos)
                        codeFor1stToken = self.getCheetahVar(plain=True)
                        self.setPos(endPos)
                        
                    ## finally
                    addBit( codeFor1stToken + WS + nextToken )
                else:
                    addBit( codeFor1stToken + WS)
            else:
                token = self.getPyToken()
                if token in ('{','(','['):
                    self.rev()
                    token = self.getExpression(enclosed=True)
                addBit(token)

        return ''.join(argStringBits)
    
    def getDefArgList(self, exitPos=None, useNameMapper=False):

        """ Get an argument list. Can be used for method/function definition
        argument lists or for #directive argument lists. Returns a list of
        tuples in the form (argName, defVal=None) with one tuple for each arg
        name.

        These defVals are always strings, so (argName, defVal=None) is safe even
        with a case like (arg1, arg2=None, arg3=1234*2), which would be returned as
        [('arg1', None),
         ('arg2', 'None'),
         ('arg3', '1234*2'),         
        ]

        This method understands *arg, and **kw

        """

        if self.peek() == '(':
            self.advance()
        else:
            exitPos = self.findEOL()  # it's a directive so break at the EOL
        argList = ArgList()
        onDefVal = False
        useNameMapper_orig = self.setting('useNameMapper')
        self.setSetting('useNameMapper', useNameMapper)

        while 1:
            if self.atEnd():
                self.setPos(enclosures[-1][1])
                raise ParseError(
                    self, msg="EOF was reached before a matching ')'"+
                    " was found for the '('")

            if self.pos() == exitPos:
                break

            c = self.peek()
            if c == ")" or self.matchDirectiveEndToken():
                break
            elif c in " \t\f\r\n":
                if onDefVal:
                    argList.addToDefVal(c)
                self.advance()
            elif c == '=':
                onDefVal = True
                self.advance()
            elif c == ",":
                argList.next()
                onDefVal = False
                self.advance()
            elif self.startswith(self.cheetahVarStartToken) and not onDefVal:
                self.advance(len(self.cheetahVarStartToken))
            elif self.matchIdentifier() and not onDefVal:
                argList.addArgName( self.getIdentifier() )
            elif onDefVal:
                if self.matchCheetahVarStart():
                    token = self.getCheetahVar()
                else:
                    token = self.getPyToken()
                    if token in ('{','(','['):
                        self.rev()
                        token = self.getExpression(enclosed=True)
                argList.addToDefVal(token)
            elif c == '*' and not onDefVal:
                varName = self.getc()
                if self.peek() == '*':
                    varName += self.getc()
                if not self.matchIdentifier():
                    raise ParseError(self)
                varName += self.getIdentifier()
                argList.addArgName(varName)
            else:
                raise ParseError(self)

                
        self.setSetting('useNameMapper', useNameMapper_orig)
        return argList.merge()
    
    def getExpression(self,
                      enclosed=False, 
                      enclosures=[], # list of tuples (char, pos), where char is ({ or [ 
                      ):

        """ Get a Cheetah expression that includes $CheetahVars and break at
        directive end tokens."""

        
        srcLen = len(self)
        exprBits = []
        while 1:
            if self.atEnd():
                if enclosures:
                    open = enclosures[-1][0]
                    close = closurePairsRev[open]
                    self.setPos(enclosures[-1][1])
                    raise ParseError(
                        self, msg="EOF was reached before a matching '" + close +
                        "' was found for the '" + open + "'")
                else:
                    break

            c = self.peek()
            
            if c in "{([":
                exprBits.append(c)
                enclosures.append( (c, self.pos()) )
                self.advance()
                
            elif enclosed and not enclosures:
                break
                
            elif c in "])}":
                if not enclosures:
                    raise ParseError(self)
                open = closurePairs[c]
                if enclosures[-1][0] == open:
                    enclosures.pop()
                    exprBits.append(c)
                else:
                    open = enclosures[-1][0]
                    close = closurePairsRev[open]
                    row, col = self.getRowCol()
                    self.setPos(enclosures[-1][1])
                    raise ParseError(
                        self, msg= "A '" + c + "' was found at line " + str(row) +
                        ", col " + str(col) +
                        " before a matching '" + close +
                        "' was found\nfor the '" + open + "'")
                self.advance()
                                
            elif c in " \f\t":
                exprBits.append(self.getWhiteSpace())
            
            elif self.matchDirectiveEndToken():
                break
            
            elif c == "\\" and self.pos()+1 < srcLen:
                eolMatch = EOLre.match(self.src(), self.pos()+1)
                if not eolMatch:
                    self.advance()
                    raise ParseError(self, msg='Line ending expected')
                self.setPos( eolMatch.end() )
            elif c in '\r\n':
                if enclosures:
                    self.advance()                    
                else:
                    break
                
            elif self.matchIdentifier():
                token = self.getIdentifier()
                exprBits.append(token)
                if token == 'for':
                    targetVars = self.getTargetVarsList()
                    exprBits.append(' ' + ', '.join(targetVars) + ' ')
                    if not enclosures:
                        self.addLocalVars(targetVars)
                else:
                    exprBits.append(self.getWhiteSpace())
                    if not self.atEnd() and self.peek() == '(':
                        exprBits.append(self.getCallArgString())
                        
                    
            elif self.matchCheetahVarStart():
                token = self.getCheetahVar()
                exprBits.append(token)
            else:
                token = self.getPyToken()
                exprBits.append(token)                    
                                        
        expression = ''.join(exprBits)
        return expression

    
class _HighLevelSemanticsParser(_LowLevelSemanticsParser):

    def initDirectives(self):
        self.directiveEaters = {

            # importing and inheritance
            'import':self.eatImport,
            'from':self.eatImport,
            'extends': self.eatExtends,
            'implements': self.eatImplements,

            # output, filtering, and caching
            'slurp': self.eatSlurp,
            'raw': self.eatRaw,
            'include': self.eatInclude,
            'cache': self.eatCache,
            'filter': self.eatFilter,
            'echo': self.eatEcho,
            'silent': self.eatSilent,

            # declaration and assignment
            'attr':self.eatAttr,
            'def': self.eatDef,
            'block': self.eatBlock,
            'set': self.eatSet,
            'settings':self.eatSettings,
            
            # flow control
            'while': self.eatWhile,
            'for': self.eatFor,
            'if': self.eatIf,
            'else': self.eatElse,
            'elif': self.eatElse,
            'pass': self.eatPass,
            'break': self.eatBreak,
            'continue': self.eatContinue,
            'stop': self.eatStop,

            # little wrappers
            'repeat': self.eatRepeat,
            'unless': self.eatUnless,

            # error handling
            'assert': self.eatAssert,
            'raise': self.eatRaise,
            'try': self.eatTry,
            'except': self.eatExcept,
            'finally': self.eatFinally,
            'errorCatcher':self.eatErrorCatcher,

            # intructions to the parser and compiler
            'breakpoint':self.eatBreakPoint,
            'compiler-settings':self.eatCompilerSettings,

            # misc
            'shBang': self.eatShbang,
            
            'end': self.eatEndDirective,
            }


        self.directiveEndEaters = {
            'def': self.eatEndDef,
            'block': self.eatEndBlock,
            
            'cache': self.eatEndCache,
            'filter': self.eatEndFilter,
            'errorCatcher':self.eatEndErrorCatcher,
            
            'while': self.eatEndWhile,
            'for': self.eatEndFor,
            'if': self.eatEndIf,
            'try': self.eatEndIf,
            
            'repeat': self.eatEndRepeat,
            'unless': self.eatEndUnless,
            
            }

    ## main parse loop

    def parse(self):
        while not self.atEnd():
            if self.matchCommentStartToken():
                self.eatComment()
            elif self.matchMultiLineCommentStartToken():
                self.eatMultiLineComment()
            elif self.matchCheetahVarStart():
                self.eatPlaceholder()
            elif self.isDirective():
                self.eatDirective()
            elif self.matchPSPStartToken():
                self.eatPSP()
            else:
                self.eatStrConstant()
                
    ## eat methods    
                
    def eatStrConstant(self):
        startPos = self.pos()
        while not self.atEnd():
            if self.matchNonStrConst():
                break
            else:
                self.advance()
        strConst = self.readTo(self.pos(), start=startPos)
        self.addStrConst(strConst)

    def eatComment(self):
        lineClearToStartToken = self.lineClearToStartToken()
        if lineClearToStartToken:
            self.delLeadingWS()
        self.getCommentStartToken()            
        comm = self.readToEOL(gobble=lineClearToStartToken)
        specialVarMatch = specialVarRE.match(comm)
        self.addComment(comm)

    def eatMultiLineComment(self):
        lineClearToStartToken = self.lineClearToStartToken()
        endOfFirstLine = self.findEOL()

        self.getMultiLineCommentStartToken()
        endPos = startPos = self.pos()
        level = 1
        while 1:
            endPos = self.pos()
            if self.atEnd():
                break
            if self.matchMultiLineCommentStartToken():
                self.getMultiLineCommentStartToken()
                level += 1
            elif self.matchMultiLineCommentEndToken():
                self.getMultiLineCommentEndToken()
                level -= 1
            if not level:
                break
            self.advance()
        comm = self.readTo(endPos, start=startPos)
        if not self.atEnd():
            self.getMultiLineCommentEndToken()
        # don't gobble
        self.addComment(comm)

    def eatPlaceholder(self):
        startPos = self.pos()
        startToken = self.getCheetahVarStartToken()
        cacheToken = self.getCacheToken()
        
        cacheInfo = self.genCacheInfo(cacheToken)
        
        if self.peek() in '({[':
            pos = self.pos()
            enclosures = [ (self.getc(), pos) ]
            self.getWhiteSpace()
        else:
            enclosures = []
        nameChunks = self.getCheetahVarNameChunks()
        if enclosures:
            restOfEnclosure = self.getCallArgString(enclosures=enclosures,
                                                    )[1:-1]
        else:
            restOfEnclosure = ''

        rawPlaceholder = self[startPos: self.pos()]
        lineCol = self.getRowCol(startPos)
        
        codeChunk  = self.genCheetahVar(nameChunks)

        ## deal with the cache
        if cacheInfo:
            cacheInfo['ID'] = repr(rawPlaceholder)[1:-1]
            self.startCacheRegion(cacheInfo, lineCol)
            
        if self.errorCatcherIsOn():            
            methodName = self.addErrorCatcher(codeChunk,
                                              rawCode=rawPlaceholder,
                                              lineCol=lineCol,
                                              )
            codeChunk = 'self.' + methodName + '(localsDict=locals())'

        self.addFilteredChunk( codeChunk + restOfEnclosure )
        self.appendToPrevChunk(' # generated from ' + repr(rawPlaceholder) )
        if self.setting('outputRowColComments'):
            self.appendToPrevChunk(' at line, col '+ str(lineCol) + '.')
        if cacheInfo:
            self.endCacheRegion()

    def eatPSP(self):
        self.getPSPStartToken()
        endToken = self.setting('PSPEndToken')
        startPos = self.pos()            
        while not self.atEnd():
            if self.peek() == endToken[0]:
                if self.matchPSPEndToken():
                    break
            self.advance()
        pspString = self.readTo(self.pos(), start=startPos).strip()
        self.addPSP(pspString)
        self.getPSPEndToken()


    ## generic directive eat methods

    def eatDirective(self):
        directiveKey = self.isDirective()
        self.directiveEaters[directiveKey]()

    def eatEndDirective(self):
        lineClearToStartToken = self.lineClearToStartToken()
        self.getDirectiveStartToken()
        self.advance(3)                 # to end of 'end'
        self.getWhiteSpace()
        pos = self.pos()
        directiveKey = False
        for key in self.directiveEndEaters.keys():
            if self.find(key) == pos:
                directiveKey = key
                break
        if not directiveKey:
            raise ParseError(self, msg='Invalid end directive')
                    
        self.directiveEndEaters[directiveKey](
            lineClearToStartToken=lineClearToStartToken)


    def eatSimpleExprDirective(self):
        lineClearToStartToken = self.lineClearToStartToken()
        endOfFirstLine = self.findEOL()
        self.getDirectiveStartToken()
        expr = self.getExpression().strip()
        self.closeDirective(lineClearToStartToken, endOfFirstLine)
        return expr

    ## specific directive eat methods
    
    def eatBreakPoint(self):
        self.setBreakPoint(self.pos())

    def eatShbang(self):
        self.getDirectiveStartToken()
        self.advance(len('shBang'))
        self.getWhiteSpace()
        shBang = self.readToEOL()
        self.addShBang(shBang.strip())

    def eatCompilerSettings(self):
        lineClearToStartToken = self.lineClearToStartToken()
        endOfFirstLine = self.findEOL()
        self.getDirectiveStartToken()
        self.advance(len('compiler-settings'))   # to end of 'settings'
        
        KWs = self.getTargetVarsList()
        self.getExpression()            # gobble any garbage
            
        self.closeDirective(lineClearToStartToken, endOfFirstLine)
        
        merge = True
        if 'nomerge' in KWs:
            merge = False
            
        if 'reset' in KWs:
            self._initializeSettings()
            self.configureParser()
            return
        elif 'python' in KWs:
            settingsReader = self.updateSettingsFromPySrcStr
        else:
            settingsReader = self.updateSettingsFromConfigStr

        settingsStr = self.readToThisEndDirective('compiler-settings')            
        
        try:
            settingsReader(settingsStr)
        except:
            out = sys.stderr
            print >> out, 'An error occurred while processing the following compiler settings.'
            print >> out, '-'*80
            print >> out, settingsStr.strip()
            print >> out, '-'*80
            print >> out, 'Please check the syntax of these settings.'
            print >> out, 'A full Python exception traceback follows.'
            raise
        self.configureParser()
    
    def eatSettings(self):
        lineClearToStartToken = self.lineClearToStartToken()
        endOfFirstLine = self.findEOL()
        self.getDirectiveStartToken()
        self.advance(len('settings'))   # to end of 'settings'

        KWs = self.getTargetVarsList()
        self.getExpression()            # gobble any garbage
        self.closeDirective(lineClearToStartToken, endOfFirstLine)

        
        merge = True
        if 'nomerge' in KWs:
            merge = False
            
        if 'reset' in KWs:
            self._initializeSettings()
            self.configureParser()
            return
        elif 'python' in KWs:
            settingsType = 'python'
        else:
            settingsType = 'ini'
        
        settingsStr = self.readToThisEndDirective('settings')
        self.addSettingsToInit(settingsStr, settingsType=settingsType)
        
        if self._templateObj:
            # note that these settings won't affect the compiler/parser settings!
            if settingsType == 'python':
                self._templateObj.updateSettingsFromPySrcStr(settingsStr, merge=merge)
            else:
                self._templateObj.updateSettingsFromConfigStr(settingsStr, merge=merge)


    def eatAttr(self):
        lineClearToStartToken = self.lineClearToStartToken()
        endOfFirstLinePos = self.findEOL()
        startPos = self.pos()
        self.getDirectiveStartToken()
        self.advance(len('attr'))
        self.getWhiteSpace()
        
        if self.matchCheetahVarStart():
            self.getCheetahVarStartToken()
        attribName = self.getIdentifier()
        self.getWhiteSpace()
        self.getAssignmentOperator()
        expr = self.getExpression()
        self.addAttribute(attribName + ' =' + expr)
        val = eval(expr,{},{})
        if self._templateObj:
            setattr(self._templateObj, attribName, val)
        self.closeDirective(lineClearToStartToken, endOfFirstLinePos)
        
    def eatDef(self):
        lineClearToStartToken = self.lineClearToStartToken()
        endOfFirstLinePos = self.findEOL()
        startPos = self.pos()
        self.getDirectiveStartToken()
        self.advance(len('def'))
        self.getWhiteSpace()
        if self.matchCheetahVarStart():
            self.getCheetahVarStartToken()
        methodName = self.getIdentifier()
        self.getWhiteSpace()
        if self.peek() == '(':
            argsList = self.getDefArgList()
            self.advance()              # past the closing ')'
            if argsList and argsList[0][0] == 'self':
                del argsList[0]
        else:
            argsList=[]
        
        if self.peek() == ':':
            self.getc()
            self.startSingleLineDef(methodName, argsList, startPos, endOfFirstLinePos)
            self.closeDirective(lineClearToStartToken, endOfFirstLinePos)
        else:
            self.startMultiLineDef(methodName, argsList, startPos, lineClearToStartToken)
        
    def eatBlock(self):
        lineClearToStartToken = self.lineClearToStartToken()
        endOfFirstLinePos = self.findEOL()
        startPos = self.pos()
        self.getDirectiveStartToken()
        self.advance(len('block'))
        self.getWhiteSpace()
        if self.matchCheetahVarStart():
            self.getCheetahVarStartToken()
        methodName = self.getIdentifier()
        self.getWhiteSpace()
        if self.peek() == '(':
            argsList = self.getDefArgList()
            self.advance()              # past the closing ')'
            if argsList and argsList[0][0] == 'self':
                del argsList[0]
        else:
            argsList=[]

        singleLiner = False
        if self.peek() == ':':
            singleLiner = True
            self.getc()
            rawDef = self.startSingleLineDef(methodName, argsList, startPos, endOfFirstLinePos)
            self.closeDirective(lineClearToStartToken, endOfFirstLinePos)
        else:
            rawDef = self.startMultiLineDef(methodName, argsList, startPos, lineClearToStartToken)
            
        self._blockMetaData[methodName] = {'raw':rawDef,
                                           'lineCol':self.getRowCol(startPos),
                                           }
        
        if self.setting('includeBlockMarkers'):
            startMarker = self.setting('blockMarkerStart')
            self.addStrConst(startMarker[0] + methodName + startMarker[1])

        if singleLiner:
            self.closeBlock(methodName)
            
            
    def startSingleLineDef(self, methodName, argsList, startPos, endPos):
        methodSrc = self[self.pos():endPos].strip()
        signature = self[startPos:endPos]

        origBP = self.breakPoint()
        origSrc = self._src
        self._src = methodSrc
        self.setPos(0)
        self.setBreakPoint(len(methodSrc))
        
        from Compiler import AutoMethodCompiler
        methodCompiler = self.spawnMethodCompiler(methodName, klass=AutoMethodCompiler)
        self.setActiveMethodCompiler(methodCompiler)
        methodCompiler.addMethDocString('Generated from ' + signature +
                                        ' at line, col ' +
                                        str(self.getRowCol(startPos)) +
                                            '.')
        ## deal with the method's argstring
        for argName, defVal in argsList:
            methodCompiler.addMethArg(argName, defVal)
        
        self.parse()
        self.commitStrConst()
        methCompiler = self.getActiveMethodCompiler()
        self.swallowMethodCompiler(methCompiler)
        
        self._src = origSrc
        self.setBreakPoint(origBP)
        self.setPos(endPos)
        return signature

        
    def startMultiLineDef(self, methodName, argsList, startPos, lineClearToStartToken=False):

        rawDef = self[startPos:self.pos()]
        self.getExpression()            # slurp up any garbage left at the end
        signature = self[startPos:self.pos()]
        endOfFirstLinePos = self.findEOL()
        self.closeDirective(lineClearToStartToken, endOfFirstLinePos)
        ## create the method compiler and register it
        
        from Compiler import AutoMethodCompiler
        methodCompiler = self.spawnMethodCompiler(methodName, klass=AutoMethodCompiler)
        self.setActiveMethodCompiler(methodCompiler)
        
        ## deal with the method's argstring
        for argName, defVal in argsList:
            methodCompiler.addMethArg(argName, defVal)

        methodCompiler.addMethDocString('Generated from ' + signature +
                                        ' at line, col ' +
                                        str(self.getRowCol(startPos)) +
                                        '.')            
        return methodName, rawDef

    def eatImport(self):
        lineClearToStartToken = self.lineClearToStartToken()
        endOfFirstLine = self.findEOL()
        self.getDirectiveStartToken()
        impStatement = self.getExpression()
        self.addImportStatement(impStatement)
        self.closeDirective(lineClearToStartToken, endOfFirstLine)

        ## this doesn't work with from math import *, etc.
        importVarNames = impStatement[impStatement.find('import') + len('import'):].split(',')
        importVarNames = [var.split()[-1] for var in importVarNames]
        self.addImportedVars(importVarNames)

        if self._templateObj:
            import Template as TemplateMod
            mod = self._templateObj._importAsDummyModule(impStatement)
            for varName in importVarNames:
                val = getattr(mod, varName.split('.')[0])
                setattr(TemplateMod, varName, val)
    
    def eatExtends(self):
        lineClearToStartToken = self.lineClearToStartToken()
        endOfFirstLine = self.findEOL()
        self.getDirectiveStartToken()
        self.advance(len('extends'))
        self.getWhiteSpace()
        self.setMainMethodName('writeBody') # change from the default 'respond'
        baseClassList = self.getTargetVarsList()
        self.setBaseClasses( baseClassList )
        mainBaseClass =  self._baseClasses[0]
        self.closeDirective(lineClearToStartToken, endOfFirstLine)
        
        ##################################################
        ## dynamically bind to and __init__ with this new baseclass
        #  - this is required for COMPILE_TIME_CACHE to work properly
        #    and for dynamic use of templates compiled directly from file
        #  - also necessary for the 'monitorSrc' fileMtime triggered recompiles
        
        if self._templateObj:
            mod = self._templateObj._importAsDummyModule('\n'.join(self._importStatements))
            newBaseClasses = []
            for baseClass in self._baseClasses:
                newBaseClasses.append( getattr(mod, baseClass))

            class newClass:
                pass
            newClass.__name__ = self._mainClassName
            newClass.__bases__ = tuple(newBaseClasses)
            self._templateObj.__class__ = newClass
            # must initialize it so instance attributes are accessible
            newClass.__init__(self._templateObj)
            
    def eatImplements(self):
        lineClearToStartToken = self.lineClearToStartToken()
        endOfFirstLine = self.findEOL()
        self.getDirectiveStartToken()
        self.advance(len('implements'))
        self.getWhiteSpace()
        self.setMainMethodName(self.getIdentifier())
        self.getExpression()  # throw away and unwanted crap that got added in
        self.closeDirective(lineClearToStartToken, endOfFirstLine)


    def eatSilent(self):
        lineClearToStartToken = self.lineClearToStartToken()
        endOfFirstLinePos = self.findEOL()
        self.getDirectiveStartToken()
        self.advance(len('silent'))
        self.getWhiteSpace()
        expr = self.getExpression()
        self.closeDirective(lineClearToStartToken, endOfFirstLinePos)
        self.addSilent(expr)

    def eatEcho(self):
        self.getDirectiveStartToken()
        self.advance(len('echo'))
        self.getWhiteSpace()
        expr = self.getExpression()
        self.closeDirective(False, self.pos())
        self.addFilteredChunk(expr)

    def eatSet(self):
        lineClearToStartToken = self.lineClearToStartToken()
        endOfFirstLine = self.findEOL()

        self.getDirectiveStartToken()
        self.advance(3)
        self.getWhiteSpace()
        if self.startswith('local'):
            self.getIdentifier()
            self.getWhiteSpace()
            isGlobal = False
        elif self.startswith('global'):
            self.getIdentifier()
            self.getWhiteSpace()
            isGlobal = True
        else:
            isGlobal = False
        
        if not self.matchCheetahVarStart():
            raise ParseError(self, msg='CheetahVar expected')
        
        cheetahVar = self.getCheetahVar(plain=True)
        
        self.getWhiteSpace()
        OP = self.getAssignmentOperator()
        expr = self.getExpression()
        
        self.closeDirective(lineClearToStartToken, endOfFirstLine)
        self.addSet(cheetahVar, OP, expr, isGlobal)
    
    def eatSlurp(self):
        if self.lineClearToStartToken():
            self.delLeadingWS()
        self.commitStrConst()
        self.readToEOL(gobble=True)

    def eatRaw(self):
        lineClearToStartToken = self.lineClearToStartToken()
        endOfFirstLinePos = self.findEOL()
        self.getDirectiveStartToken()
        self.getExpression()
        self.closeDirective(lineClearToStartToken, endOfFirstLinePos)

        rawBlock = self.readToThisEndDirective('raw')
        self.addStrConst(rawBlock)
    
    def eatInclude(self):
        lineClearToStartToken = self.lineClearToStartToken()
        endOfFirstLinePos = self.findEOL()
        self.getDirectiveStartToken()
        self.advance(len('include'))

        self.getWhiteSpace()
        includeFrom = 'file'
        raw = False
        if self.startswith('raw'):
            self.advance(3)
            raw=True
            
        self.getWhiteSpace()            
        if self.startswith('source'):
            self.advance(len('source'))
            includeFrom = 'str'
            self.getWhiteSpace()
            if not self.peek() == '=':
                raise ParseError(self)
            self.advance()
            
        expr = self.getExpression()
            
        self.closeDirective(lineClearToStartToken, endOfFirstLinePos)
        self.addWriteChunk('self._includeCheetahSource(' + expr + ', trans=trans, ' +
                           'includeFrom="' + includeFrom + '", raw=' + str(raw) +
                           ')')

    def eatCache(self):
        lineClearToStartToken = self.lineClearToStartToken()
        endOfFirstLinePos = self.findEOL()
        lineCol = self.getRowCol()
        self.getDirectiveStartToken()
        self.advance(len('cache'))
        startPos = self.pos()
        argList = self.getDefArgList(useNameMapper=True)
        self.closeDirective(lineClearToStartToken, endOfFirstLinePos)
        cacheInfo = self.genCacheInfoFromArgList(argList)
        self.startCacheRegion(cacheInfo, lineCol)


    def eatFilter(self):
        lineClearToStartToken = self.lineClearToStartToken()
        endOfFirstLinePos = self.findEOL()

        self.getDirectiveStartToken()
        self.advance(len('filter'))
        self.getWhiteSpace()
        
        if self.matchCheetahVarStart():
            isKlass = True
            theFilterExpr = self.getExpression()
        else:
            isKlass = False
            theFilter = self.getIdentifier()
            self.getWhiteSpace()
        
        self.closeDirective(lineClearToStartToken, endOfFirstLinePos)

        if isKlass:
            self.addChunk('filter = self._currentFilter = ' + theFilterExpr.strip() +
                          '(self).filter')
        else:
            if theFilter.lower() == 'none':
                self.addChunk('filter = self._initialFilter')
            else:
                # is string representing the name of builtin filter
                self.addChunk('filterName = ' + repr(theFilter))
                self.addChunk('if self._filters.has_key("' + theFilter + '"):')
                self.indent()
                self.addChunk('filter = self._currentFilter = self._filters[filterName]')
                self.dedent()
                self.addChunk('else:')
                self.indent()
                self.addChunk('filter = self._currentFilter = \\\n\t\t\tself._filters[filterName] = '
                              + 'getattr(self._filtersLib, filterName)(self).filter')
                self.dedent()
        
    def eatErrorCatcher(self):
        lineClearToStartToken = self.lineClearToStartToken()
        endOfFirstLinePos = self.findEOL()

        self.getDirectiveStartToken()
        self.advance(len('errorCatcher'))
        self.getWhiteSpace()
        self.turnErrorCatcherOn()
        theChecker = self.getIdentifier()
        if self._templateObj:
            self._templateObj._errorCatcher = \
                   getattr(ErrorCatchers, theChecker)(self._templateObj)
            
        self.closeDirective(lineClearToStartToken, endOfFirstLinePos)
        self.addChunk('if self._errorCatchers.has_key("' + theChecker + '"):')
        self.indent()
        self.addChunk('self._errorCatcher = self._errorCatchers["' +
            theChecker + '"]')
        self.dedent()
        self.addChunk('else:')
        self.indent()
        self.addChunk('self._errorCatcher = self._errorCatchers["'
                      + theChecker + '"] = ErrorCatchers.'
                      + theChecker + '(self)'
                      )
        self.dedent()
        
    def eatWhile(self):
        self.addWhile(self.eatSimpleExprDirective())

    def eatFor(self):
        lineClearToStartToken = self.lineClearToStartToken()
        endOfFirstLinePos = self.findEOL()

        self.getDirectiveStartToken()
        expr = self.getExpression()
        self.closeDirective(lineClearToStartToken, endOfFirstLinePos)
        self.addFor(expr)
        
    def eatIf(self):
        self.addIf(self.eatSimpleExprDirective())
    
    def eatElse(self):
        """else, elif and else if"""
        self.addElse(self.eatSimpleExprDirective())

    def eatTry(self):
        self.addTry(self.eatSimpleExprDirective())

    def eatExcept(self):
        self.addExcept(self.eatSimpleExprDirective())

    def eatFinally(self):
        self.addFinally(self.eatSimpleExprDirective())


    def eatPass(self):
        self.addChunk(self.eatSimpleExprDirective())

    def eatAssert(self):
        self.addChunk(self.eatSimpleExprDirective())

    def eatRaise(self):
        self.addChunk(self.eatSimpleExprDirective())

    def eatBreak(self):
        self.addChunk(self.eatSimpleExprDirective())

    def eatContinue(self):
        self.addChunk(self.eatSimpleExprDirective())

    def eatStop(self):
        self.addStop(self.eatSimpleExprDirective())

    def eatRepeat(self):
        lineClearToStartToken = self.lineClearToStartToken()
        endOfFirstLinePos = self.findEOL()
        self.getDirectiveStartToken()
        self.advance(len('repeat'))
        expr = self.getExpression()
        self.closeDirective(lineClearToStartToken, endOfFirstLinePos)
        self.addFor('for i in range(' + expr + ')')

    def eatUnless(self):
        lineClearToStartToken = self.lineClearToStartToken()
        endOfFirstLinePos = self.findEOL()
        self.getDirectiveStartToken()
        self.advance(len('unless'))
        expr = self.getExpression()
        self.closeDirective(lineClearToStartToken, endOfFirstLinePos)
        self.addIf('if not ' + expr)

    ## end directive eaters

    def eatEndDef(self, lineClearToStartToken=False):
        endOfFirstLinePos = self.findEOL()
        self.getExpression()
        self.closeDirective(lineClearToStartToken, endOfFirstLinePos)
        self.commitStrConst()
        methCompiler = self.getActiveMethodCompiler()
        self.swallowMethodCompiler(methCompiler)

    def eatEndBlock(self, lineClearToStartToken=False):
        endOfFirstLinePos = self.findEOL()
        self.getExpression()
        self.closeDirective(lineClearToStartToken, endOfFirstLinePos)
        methCompiler = self.getActiveMethodCompiler()
        methodName = methCompiler.methodName()
        if self.setting('includeBlockMarkers'):
            endMarker = self.setting('blockMarkerEnd')
            methCompiler.addStrConst(endMarker[0] + methodName + endMarker[1])
        if hasattr(self, 'commitStrConst'):
            self.commitStrConst()
        self.swallowMethodCompiler(methCompiler)
        self.closeBlock(methodName)

    def closeBlock(self, methodName):
        metaData = self._blockMetaData[methodName] 
        rawDirective = metaData['raw']
        lineCol = metaData['lineCol']
        
        ## insert the code to call the block, caching if #cache directive is on
        codeChunk = 'self.' + methodName + '(trans=trans)'
        self.addChunk(codeChunk)
        
        self.appendToPrevChunk(' # generated from ' + repr(rawDirective) )
        if self.setting('outputRowColComments'):
            self.appendToPrevChunk(' at line, col '+ str(lineCol) + '.')

    def eatEndCache(self, lineClearToStartToken=False):
        endOfFirstLinePos = self.findEOL()
        self.getExpression()
        self.closeDirective(lineClearToStartToken, endOfFirstLinePos)
        self.endCacheRegion()

    def eatEndFilter(self, lineClearToStartToken=False):
        endOfFirstLinePos = self.findEOL()
        self.getExpression()
        self.closeDirective(lineClearToStartToken, endOfFirstLinePos)
        self.addChunk('filter = self._initialFilter')        

    def eatEndErrorCatcher(self, lineClearToStartToken=False):
        endOfFirstLinePos = self.findEOL()
        self.getExpression()
        self.closeDirective(lineClearToStartToken, endOfFirstLinePos)
        self.turnErrorCatcherOff()

    def eatDedentDirective(self, lineClearToStartToken=False):        
        endOfFirstLinePos = self.findEOL()
        self.getExpression()
        self.closeDirective(lineClearToStartToken, endOfFirstLinePos)
        self.commitStrConst()            
        self.dedent()

    # aliases
    eatEndWhile = eatDedentDirective
    eatEndIf = eatDedentDirective
    eatEndFor = eatDedentDirective
    eatEndTry = eatDedentDirective
    eatEndRepeat = eatDedentDirective
    eatEndUnless = eatDedentDirective

##################################################
## Make an alias to export
    
Parser = _HighLevelSemanticsParser
