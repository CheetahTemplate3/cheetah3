#!/usr/bin/env python
# $Id: TemplateCmdLineIface.py,v 1.11 2002/11/10 20:44:11 hierro Exp $

"""Provides a command line interface to compiled Cheetah template modules.

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@damnsimple.com>
Version: $Revision: 1.11 $
Start Date: 2001/12/06
Last Revision Date: $Date: 2002/11/10 20:44:11 $
"""
__author__ = "Tavis Rudd <tavis@damnsimple.com>"
__revision__ = "$Revision: 1.11 $"[11:-2]

##################################################
## DEPENDENCIES

import sys
import os
import getopt
import os.path

try:
    from cPickle import load
except ImportError:
    from pickle import load


#intra-package imports ...
from _properties import Version

##################################################
## GLOBALS & CONTANTS

try:
    True,False
except NameError:
    True, False = (1==1),(1==0)

class Error(Exception):
    pass

class CmdLineIface:
    """A command line interface to compiled Cheetah template modules."""

    def __init__(self, templateObj,
                 scriptName=os.path.basename(sys.argv[0]),
                 cmdLineArgs=sys.argv[1:]):

        self._template = templateObj
        self._scriptName = scriptName
        self._cmdLineArgs = cmdLineArgs

    def run(self):
        """The main program controller."""
        
        self._processCmdLineArgs()
        print self._template
        
    def _processCmdLineArgs(self):
        try:
            self._opts, self._args = getopt.getopt(
                self._cmdLineArgs, 'h', ['help',
                                            'env',
                                            'pickle=',
                                            ])

        except getopt.GetoptError, v:
            # print help information and exit:
            print v
            print self.usage()
            sys.exit(2)
        
        for o, a in self._opts:
            if o in ('-h','--help'):
                print self.usage()
                sys.exit()
            if o == '--env':
                self._template._searchList.insert(0, os.environ)
            if o == '--pickle':
                if a == '-':
                    unpickled = load(sys.stdin)
                    self._template._searchList.insert(0, unpickled)
                else:
                    f = open(a)
                    unpickled = load(f)
                    f.close()
                    self._template._searchList.insert(0, unpickled)

    def usage(self):
        return """Cheetah %(Version)s template module command-line interface

Usage
-----
  %(scriptName)s [OPTION]

Options
-------
  -h, --help                 Print this help information
  
  --env                      Use shell ENVIRONMENT variables to fill the
                             $placeholders in the template.
                             
  --pickle <file>            Use a variables from a dictionary stored in Python
                             pickle file to fill $placeholders in the template.
                             If <file> is - stdin is used: 
                             '%(scriptName)s --pickle -'

Description
-----------

This interface allows you to execute a Cheetah template from the command line
and collect the output.  It can prepend the shell ENVIRONMENT or a pickled
Python dictionary to the template's $placeholder searchList, overriding the
defaults for the $placeholders.

""" % {'scriptName':self._scriptName,
       'Version':Version,
       }

# vim: shiftwidth=4 tabstop=4 expandtab
