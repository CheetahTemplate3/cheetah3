#!/usr/bin/env python
# $Id: CheetahCompile.py,v 1.5 2001/11/04 20:12:11 tavis_rudd Exp $
"""A command line compiler for turning Cheetah files (.tmpl) into Webware
servlet files (.py).

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
Version: $Revision: 1.5 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2001/11/04 20:12:11 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.5 $"[11:-2]

##################################################
## DEPENDENCIES

import sys
import re
import os
import getopt
from os.path import \
     walk as pathWalk, \
     split as pathSplit, \
     splitext as pathSplitext, \
     exists

from glob import glob

#intra-package imports ...
from Version import version
from Template import Template
from Compiler import Compiler

##################################################
## GLOBALS & CONTANTS

True = (1==1)
False = (1==0)
    
class CheetahCompile:
    """A command-line compiler for Cheetah .tmpl files."""

    CHEETAH_EXTENSION = '.tmpl'
    SERVLET_EXTENSION = '.py'
    SERVLET_BACKUP_EXT = '.py_bak'

    def __init__(self):
        self.makeGenFile = False

    def run(self):
        """The main program controller."""
        try:
            opts, args = getopt.getopt( sys.argv[1:], 'hpdR', [])

        except getopt.GetoptError, v:
            # print help information and exit:
            print v
            self.usage()
            sys.exit(2)
        if not (opts or args):
            self.usage()
            sys.exit()
        
        for o, a in opts:
            if o in ('-h',):
                self.usage()
                sys.exit()
            if o in ('-R',):
                if not args:
                    args = ['.']
                for dir in args:
                    self.recursiveCompile(dir)
                sys.exit()
            if o in ('-d',):
                if not args:
                    args = ['.']
                for dir in args:
                    self.compileDir(dir)
                sys.exit()
            if o in ('-p',):
                for fileName in args:
                    className = os.path.split( os.path.splitext(fileName)[0] )[1]
                    print Compiler(file=fileName, moduleName=className, mainClassName=className)
                sys.exit()
                    
        for fileName in args:
            baseName = os.path.splitext(fileName)[0]
            self.compileFile(baseName)
    
    def recursiveCompile(self, dir='.', backupServletFiles=True):
        """Recursively walk through a directory tree and compile Cheetah files."""
        pending = [dir]
        while pending:
            dir = pending.pop()
            ## add sub-dirs
            for shortname in os.listdir(dir):
                path = os.path.join(dir, shortname)
                if os.path.isdir(path):
                    pending.append(path)
                    
            ## do it!
            self.compileDir(dir, backupServletFiles=backupServletFiles) 

            
    def compileFile(self, fileNameMinusExt):
        """Compile an single Cheetah file.  """
    
        srcFile = fileNameMinusExt + self.CHEETAH_EXTENSION
        className = os.path.split(fileNameMinusExt)[1]
        genCode = str(Compiler(file=srcFile, moduleName=className, mainClassName=className))
    
        fp = open(fileNameMinusExt + self.SERVLET_EXTENSION,'w')
        fp.write(genCode)
        fp.close()
    
        if self.makeGenFile and not os.path.exists(fileNameMinusExt +
                                            self.SERVLET_EXTENSION):
            code = self.inheritFromGenFile(fileNameMinusExt)
            fp = open(fileNameMinusExt + self.SERVLET_EXTENSION, "w")
            fp.write(code)
            fp.close()

    
    def compileDir(self, dirName='.', backupServletFiles=True):
        """Compile all the Cheetah files in a directory."""
        
        cheetahFiles = glob(dirName + '/*' + self.CHEETAH_EXTENSION)
        namesMinusExt = [pathSplitext(fileName)[0] for fileName in cheetahFiles] 
    
        if backupServletFiles:
            for i in range(len(namesMinusExt)):
                if exists( namesMinusExt[i] + self.SERVLET_EXTENSION):
                    print 'backing up', namesMinusExt[i] + \
                          self.SERVLET_EXTENSION
                    os.rename(namesMinusExt[i] + self.SERVLET_EXTENSION,
                              namesMinusExt[i] + self.SERVLET_BACKUP_EXT)
    
        for name in namesMinusExt:
            self.compileFile(name)
    
    def usage(self):
        print \
"""Cheetah %(version)s command-line compiler by %(author)s

Compiles Cheetah files (.tmpl) into Webware servlet files (.py)

Usage:
  %(scriptName)s -h                 ---> print this help and exit
  %(scriptName)s [-p] filename      ---> compile 'filename'
  %(scriptName)s -d dir        ---> compile all files in dir, output to new
                                          files with the .py extension
  %(scriptName)s -R dir        ---> same as -d, but recursively on subdirs
                                          
Options:
  -p                                 ---> print output to stdout rather than to file
  
""" % {'scriptName':os.path.basename(sys.argv[0]),
       'version':version,
       'author':'Tavis Rudd',
       }


    
##################################################
## if run from the command line
if __name__ == '__main__':

    CheetahCompile().run()


