#!/usr/bin/env python
# $Id: CheetahCompile.py,v 1.9 2001/11/25 03:04:32 tavis_rudd Exp $
"""A command line compiler for turning Cheetah files (.tmpl) into Webware
servlet files (.py).

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
Version: $Revision: 1.9 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2001/11/25 03:04:32 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.9 $"[11:-2]

##################################################
## DEPENDENCIES

import sys
import re
import os
import getopt
import os.path

from glob import glob
import shutil

#intra-package imports ...
from Version import version
from Template import Template
from Compiler import Compiler

##################################################
## GLOBALS & CONTANTS

True = (1==1)
False = (1==0)

class Error(Exception):
    pass
    
class CheetahCompile:
    """A command-line compiler for Cheetah .tmpl files."""

    CHEETAH_EXTENSION = '.tmpl'
    SERVLET_EXTENSION = '.py'
    SERVLET_BACKUP_EXT = '.py_bak'
    GENERATED_EXT = '.html'
    
    def __init__(self):
        self.makeGenFile = False
        self.compileDirectories = False
        self.recurseDirectories = False
        self.writeGenerated = False
        self.printGenerated = False
        self.compiledFiles = []

    def run(self):
        """The main program controller."""
        try:
            opts, args = getopt.getopt( sys.argv[1:], 'hpdRw', [])

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
                self.compileDirectories = True
                self.recurseDirectories = True
            if o in ('-d',):
                self.compileDirectories = True
            if o in ('-p',):
                self.printGenerated = True
            if o in ('-w',):
                self.writeGenerated = True
                    
        if not args and self.compileDirectories:
            args = ["."]
        for fileName in args:
            self.processFile(fileName)
        if self.writeGenerated:
            for fileName in self.compiledFiles:
                self.generate(fileName)

    def processFile(self, fileName):
        if os.path.isdir(fileName):
            if not self.compileDirectories:
                return
            for file in os.listdir(fileName):
                file = os.path.join(fileName, file)
                if os.path.isdir(file):
                    if self.recurseDirectories:
                        self.processFile(file)
                    continue
                extension = os.path.splitext(file)[1]
                if extension == self.CHEETAH_EXTENSION:
                    self.processFile(file)
        else:
            baseName = os.path.splitext(fileName)[0]
            if not re.match(r'[a-zA-Z_][a-zA-Z_0-9]*$',baseName):
                raise Error(
                    "The filename %s contains invalid characters.  It must" +
                    " be named according to the same rules as Python modules."
                    % fileName)
            
            self.compileFile(baseName)

            
    def compileFile(self, fileNameMinusExt):
        """Compile an single Cheetah file.  """


        self.compiledFiles.append(fileNameMinusExt)
        srcFile = fileNameMinusExt + self.CHEETAH_EXTENSION
        className = os.path.split(fileNameMinusExt)[1]
        genCode = str(Compiler(file=srcFile, moduleName=className,
                               mainClassName=className))

        if not self.printGenerated or self.writeGenerated:
            outputModuleFilename = fileNameMinusExt + self.SERVLET_EXTENSION
            if os.path.exists(outputFilename):
                shutil.copyfile(outputModuleFilename,
                                fileNameMinusExt + self.SERVLET_BACKUP_EXT)
            fp = open(outputModuleFilename,'w')
            fp.write(genCode)
            fp.close()
            
        if self.printGenerated:
            print genCode

    def generate(self, fileNameMinusExt):
        ## @@IB: this sys.path is a hack
        sys.path = [os.path.dirname(fileNameMinusExt)] + sys.path
        try:
            mod = __import__(os.path.basename(fileNameMinusExt))
            klass = getattr(mod, os.path.basename(fileNameMinusExt))
            value = str(klass())
        except:
            sys.stderr.write('Exception raised while trying to write file %s\n'
                             % repr(fileNameMinusExt))
        else:
            fp = open(fileNameMinusExt + self.GENERATED_EXT, "w")
            fp.write(value)
            fp.close()

        
    def usage(self):
        print \
"""Cheetah %(version)s command-line compiler by %(author)s

Compiles Cheetah files (.tmpl) into Webware servlet files (.py)

Usage:
  %(scriptName)s [OPTION] FILES
  %(scriptName)s [OPTION] {-R|-d} FILES/DIRECTORIES

  -R                          Recurse subdirectories
  -d                          Compile all *.tmpl files in directory
  -p                          Print generated Python code to stdout
  -w                          Write output of template to *.html
""" % {'scriptName':os.path.basename(sys.argv[0]),
       'version':version,
       'author':'Tavis Rudd',
       }


    
##################################################
## if run from the command line
if __name__ == '__main__':

    CheetahCompile().run()


