#!/usr/bin/env python
# $Id: Lexer.py,v 1.2 2001/10/10 06:47:41 tavis_rudd Exp $
"""Lexer base-class for Cheetah's Parser

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
Version: $Revision: 1.2 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/10/10 06:47:41 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.2 $"[11:-2]

##################################################
## DEPENDENCIES

from tokenize import pseudoprog

# intra-package imports ...
from SettingsManager import SettingsManager
from SourceReader import SourceReader

##################################################
## CONSTANTS & GLOBALS

True = (1==1)
False = (0==1)

##################################################
## CLASSES

class LexError(Exception): pass

class PythonLexer(SettingsManager, SourceReader):
    
    def __init__(self, src, filename=None, breakPoint=None):
        SourceReader.__init__(self, src, filename=filename, breakPoint=breakPoint)
        
        from Parser import tripleQuotedStringStarts, tripleQuotedStringREs
        self.tripleQuotedStringStarts = tripleQuotedStringStarts
        self.tripleQuotedStringREs = tripleQuotedStringREs

    def matchPyToken(self):
        match = pseudoprog.match(self.src(), self.pos())
        
        if match and match.group() in self.tripleQuotedStringStarts:
            TQSmatch = self.tripleQuotedStringREs[match.group()].match(self.src(), self.pos())
            if TQSmatch:
                return TQSmatch
        return match
        
    def getPyToken(self):
        match = self.matchPyToken()
        if match is None:
            from Parser import ParseError
            raise ParseError(self)
        elif match.group() in self.tripleQuotedStringStarts:
            from Parser import ParseError
            raise ParseError(self, msg='Malformed triple-quoted string')
        return self.readTo(match.end())
        

class CheetahLexer(PythonLexer):

    def matchCheetahToken(self):
        pass
    
    def getCheetahToken(self):
        pass
        #match = self.matchCheetahToken()
        #if match is None:
        #    raise self.ParseError(self)
        #elif match.group() in self.tripleQuotedStringStarts:
        #    raise self.ParseError(self, msg='Malformed triple-quoted string')
        #return self.readTo(match.end())

##################################################
## ALIAS TO LEXER
    
Lexer = CheetahLexer
