#!/usr/bin/env python
# $Id: Indenter.py,v 1.2 2002/07/01 03:00:02 hierro Exp $
"""Indentation maker.

This version is based directly on code by Robert Kuzelj
<robert_kuzelj@yahoo.com> and uses his directive syntax.  Some classes and
attributes have been renamed.  Indentation is output via
$self._indenter.indent() to prevent '_indenter' being looked up on the
searchList and another one being found.  The directive syntax will
soon be changed somewhat.

Meta-Data
================================================================================
Author: Mike Orr <iron@mso.oz.net>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.2 $
Start Date: 2001/11/07
Last Revision Date: $Date: 2002/07/01 03:00:02 $
""" 
__author__ = "Mike Orr <iron@mso.oz.net>"
__revision__ = "$Revision: 1.2 $"[11:-2]

##################################################
## DEPENDENCIES

import re
import sys

##################################################
## CONSTANTS & GLOBALS ##

try:
    True,False
except NameError:
    True, False = (1==1),(1==0)

##################################################
## PRIVATE FUNCTIONS


##################################################
## PUBLIC FUNCTIONS



def indentize(source):
    return IndentProcessor().process(source)

def parse(source):
    d = R"#indent[ \t]+([\w+-]+)[ \t]+(.*?)(#|$)"
    d = R"#indent[ \t]+([\w+-]+)[ \t]*(.*?)"
    INDENT_DIRECTIVE = re.compile(d)
    for lin in source.splitlines(True):
        print lin,
        pos = 0
        while 1:
            m = INDENT_DIRECTIVE.search(lin, pos)
            if m is None:
                break
            print m.groups()
            pos = m.end()

def test():
    from Cheetah.Tests.SyntaxAndOutput import Indenter as I
    for source in (I.source1, I.source2, I.source3, I.source4):
        print "===TEST==="
        parse(source)
    



##################################################
## PUBLIC CLASSES


class IndentProcessor:
    """Preprocess #indent tags."""
    LINE_SEP = '\n'
    ARGS = "args"
    INDENT_DIR = re.compile(r'[ \t]*#indent[ \t]*(?P<args>.*)')
    DIRECTIVE = re.compile(r"[ \t]*#")
    WS = "ws"
    WHITESPACES = re.compile(r"(?P<ws>[ \t]*)")

    INC = "++"
    DEC = "--"
    
    SET = "="
    CHAR = "char"
    
    ON = "on"
    OFF = "off"

    PUSH = "push"
    POP = "pop"
    
    def process(self, _txt):
        result = []

        for line in _txt.splitlines():
            match = self.INDENT_DIR.match(line)
            if match:
                #is indention directive
                args = match.group(self.ARGS).strip()
                if args == self.ON:
                    line = "#silent $self._indenter.on()"
                elif args == self.OFF:
                    line = "#silent $self._indenter.off()"
                elif args == self.INC:
                    line = "#silent $self._indenter.inc()"
                elif args == self.DEC:
                    line = "#silent $self._indenter.dec()"
                elif args.startswith(self.SET):
                    level = int(args[1:])
                    line = "#silent $self._indenter.setLevel(%(level)d)" % {"level":level}
                elif args.startswith('chars'):
                    #self.indentChars = eval(args.split('=')[1])
                    indentChars = self.indentChars = eval(args[5:])
                    line = "#silent $self._indenter.setChars(%(indentChars)s)" % {"indentChars": `indentChars`}
                elif args.startswith(self.PUSH):
                    line = "#silent $self._indenter.push()"
                elif args.startswith(self.POP):
                    line = "#silent $self._indenter.pop()"
            else:
                match = self.DIRECTIVE.match(line)
                if not match:
                    #is not another directive
                    match = self.WHITESPACES.match(line)
                    if match:
                        size = len(match.group("ws").expandtabs(4))
                        line = ("${self._indenter.indent(%(size)d)}" % {"size":size}) + line.lstrip()
                    else:
                        line = "${self._indenter.indent(0)}" + line
            result.append(line)

        return self.LINE_SEP.join(result)

class Indenter:
    """A class that keeps track of the current indentation level.
    .indent() returns the appropriate amount of indentation.
    """
    def __init__(self):
        self.On = 1
        self.Level = 0
        self.Chars = "\t" #" "*4
        self.LevelStack = []
    def on(self):
        self.On = 1
    def off(self):
        self.On = 0
    def inc(self):
        self.Level += 1
    def dec(self):
        """decrement can only be applied to values greater zero
            values below zero don't make any sense at all!"""
        if self.Level > 0:
            self.Level -= 1
    def push(self):
        self.LevelStack.append(self.Level)
    def pop(self):
        """the levestack can not become -1. any attempt to do so
           sets the level to 0!"""
        if len(self.LevelStack) > 0:
            self.Level = self.LevelStack.pop()
        else:
            self.Level = 0
    def setLevel(self, _level):
        """the leve can't be less than zero. any attempt to do so
           sets the level automatically to zero!"""
        if _level < 0:
            self.Level = 0
        else:
            self.Level = _level
    def setChar(self, _chars):
        self.Chars = _chars
    def indent(self, _default=0):
        if self.On:
            return self.Chars * self.Level
        else:
            return " " * _default


# vim: shiftwidth=4 tabstop=4 expandtab
