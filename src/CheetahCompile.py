#!/usr/bin/env python
# $Id: CheetahCompile.py,v 1.28 2002/03/28 19:36:35 tavis_rudd Exp $
"""A command line compiler for turning Cheetah files (.tmpl) into Webware
servlet files (.py).

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
Version: $Revision: 1.28 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2002/03/28 19:36:35 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__revision__ = "$Revision: 1.28 $"[11:-2]

##################################################
## DEPENDENCIES

import sys
import re
import os
import getopt
import os.path
import traceback
import imp

from glob import glob
import shutil

#intra-package imports ...
from _properties import Version
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
    BACKUP_SUFFIX = '_bak'
    GENERATED_EXT = '.html'
    
    RECURSIVE = False
    MAKE_BACKUPS = True
    VERBOSE = False
    
    WRITE_OUTPUT = False
    PRINT_GENERATED = False
    
    def __init__(self, scriptName=os.path.basename(sys.argv[0]),
                 cmdLineArgs=sys.argv[1:]):

        self._scriptName = scriptName
        self._cmdLineArgs = cmdLineArgs

    def run(self):
        """The main program controller."""
        
        self._processCmdLineArgs()

        if self._args == ["-"]:          # piped input
            print Compiler(sys.stdin.read())
        else:
            self._buildFileList()
            self._processFileList()
        
    def _processCmdLineArgs(self):
        try:
            self._opts, self._args = getopt.getopt(
                self._cmdLineArgs, 'hpdRwv', ['help'])

        except getopt.GetoptError, v:
            # print help information and exit:
            print v
            self.usage()
            sys.exit(2)
        
        for o, a in self._opts:
            if o in ('-h', '--help'):
                self.usage()
                sys.exit()
            if o in ('-R',):
                self.RECURSIVE = True
            if o in ('-p',):
                self.PRINT_GENERATED = True
            if o in ('-w',):
                self.WRITE_OUTPUT = True
            if o in ('-v',):
                self.VERBOSE = True


    def _buildFileList(self):
        if not self._args:
            self._args = ["."]
            
        pending = self._args[:]
        self._fileList = []
        addFile = self._fileList.append

        while pending:
            entry = pending.pop()
            if os.path.isdir(entry):
                for fileOrDir in os.listdir(entry):
                    fileOrDir = os.path.join(entry, fileOrDir)
                    if os.path.isdir(fileOrDir):
                        if self.RECURSIVE:
                            pending.append(fileOrDir)
                        continue
                    if self._isTemplateFile(fileOrDir):
                        addFile(fileOrDir)
            else:
                addFile(entry)
            
    def _isTemplateFile(self, filename):
        return os.path.splitext(filename)[1] == self.CHEETAH_EXTENSION

    def _processFileList(self):
        self._compiledFiles = []
        for file in self._fileList:
            self._processFile(file) # it appends to self._compiledFiles
            
        if self.WRITE_OUTPUT:
            for fileName in self._compiledFiles:
                self._generate(fileName)

    def _processFile(self, fileName):
        print 'Compiling %s ' % (fileName)
        
        srcFile = fileName
        fileNameMinusExt = os.path.splitext(fileName)[0]
        className = os.path.split(fileNameMinusExt)[1]        
        pyCode = self._compileFile(srcFile, className)
        
        self._compiledFiles.append(fileNameMinusExt)

        if not self.PRINT_GENERATED or self.WRITE_OUTPUT:
            outputModuleFilename = fileNameMinusExt + self.SERVLET_EXTENSION

            if self.MAKE_BACKUPS and os.path.exists(outputModuleFilename):
                print '  Backing up %s before saving new version of %s' % (
                    outputModuleFilename, srcFile )
                
                shutil.copyfile(outputModuleFilename,
                                outputModuleFilename + self.BACKUP_SUFFIX)

            print '  Saving compiled version of %s -> %s' % (
                srcFile, outputModuleFilename)
                
            fp = open(outputModuleFilename,'w')
            fp.write(pyCode)
            fp.close()
            
        if self.PRINT_GENERATED:
            print pyCode

    def _compileFile(self, srcFile, className):
        """Compile an single Cheetah file.  """

        if not re.match(r'[a-zA-Z_][a-zA-Z_0-9]*$', className):
            raise Error(
                "The filename %s contains invalid characters.  It must" \
                " be named according to the same rules as Python modules."
                % srcFile)
        pyCode = str(Compiler(file=srcFile, moduleName=className,
                               mainClassName=className))
        return pyCode

            
    def _generate(self, fileNameMinusExt):
        
        """Writes the output of a cheetah template file to an .html file with
        the same basename."""

        oldSysPath = sys.path[:]       
        try:
            outputFilename = fileNameMinusExt + self.GENERATED_EXT
            dirname, basename = os.path.split(fileNameMinusExt)        
            ## @@IB: this sys.path is a hack
            sys.path = [dirname] + sys.path
            
            print 'Writing the output of the template %s -> %s' % (
                fileNameMinusExt, outputFilename)

            fp, pathname, stuff = imp.find_module(basename, [dirname])
            mod = imp.load_module(basename, fp, pathname, stuff)
            klass = getattr(mod, basename)
            value = str(klass())
        except:
            sys.stderr.write(
                'An error occurred while trying to import the compiled template %s\n'
                % repr(fileNameMinusExt))
            traceback.print_exc(file=sys.stderr)
        else:
            if self.MAKE_BACKUPS and os.path.exists(outputFilename):
                print '  Backing up %s before saving new version.' % (outputFilename,)
                
                shutil.copyfile(outputFilename,
                                outputFilename + self.BACKUP_SUFFIX)

            try:
                fp = open(outputFilename, "w")
                fp.write(value)
                fp.close()
            except:
                sys.stderr.write('Exception raised while trying to write file %s\n'
                                 % repr(fileNameMinusExt))
                traceback.print_exc(file=sys.stderr)
            
        sys.path = oldSysPath
        
    def usage(self):
        print \
"""Cheetah %(Version)s command-line compiler by %(author)s

Compiles Cheetah files (.tmpl) into Webware servlet modules (.py)

Usage:
  %(scriptName)s [OPTIONS] FILES/DIRECTORIES
  %(scriptName)s [OPTIONS] -  (accept a file on stdin)
  -R                          Recurse subdirectories
  -p                          Print generated Python code to stdout
  -w                          Write output of template files to *.html
  -v                          Be verbose
  -h | --help                 Print this help message
""" % {'scriptName':self._scriptName,
       'Version':Version,
       'author':'Tavis Rudd and Ian Bicking',
       }
   
##################################################
## if run from the command line
if __name__ == '__main__':

    CheetahCompile().run()

