#!/usr/bin/env python
# $Id: Compiler.py,v 1.3 2001/07/16 03:43:28 tavis_rudd Exp $
"""A command line compiler for turning Cheetah files (.tmpl) into Webware
servlet files (.py).

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.3 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2001/07/16 03:43:28 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.3 $"[11:-2]

##################################################
## DEPENDENCIES ##

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
from Delimiters import delimiters
from Version import version

##################################################
## GLOBALS & CONTANTS ##

True = (1==1)
False = (1==0)

CHEETAH_EXTENSION = '.tmpl'
SERVLET_EXTENSION = '.py'
SERVLET_BACKUP_EXT = '.py_bak'

extendDirectiveRE = delimiters['extendDirective']
                    
##################################################
## FUNCTIONS ##
    
def wrapTemplateCode(templateExt, name):
    """Wrap a template definition string in the boiler-plate code needed to create a
    Webware servlet."""
    
    parentTemplate = [False,]
    def extendDirectiveProcessor(match, parentTemplate=parentTemplate):
        """process any #redefine directives that are found in the template extension""" 
        parentTemplate[0] = match.group('parent').strip()
        return '' # strip the directive from the extension
    
    templateExt = extendDirectiveRE.sub(extendDirectiveProcessor, templateExt)
    parentTemplate = parentTemplate[0]
    
    if parentTemplate:
        parentServlet = parentTemplate.split('.')[-1]
        servletCode = "templateExt = r'''" + templateExt
        servletCode += """'''
from %(parentModule)s import %(parentServlet)s

class %(name)s(%(parentServlet)s):
    def initializeTemplate(self):
        %(parentServlet)s.initializeTemplate(self)
        self.extendTemplate(templateExt)

""" %  {'parentModule': parentTemplate,
        'parentServlet': parentServlet,
        'name': name
        }
    else:
        servletCode = "templateExt = r'''" + templateExt
        servletCode += """'''
from Cheetah.Servlet import TemplateServlet

class %(name)s(TemplateServlet):
    def __init__(self):
        TemplateServlet.__init__(self, template=templateExt)

""" % {'name':name}

    return servletCode


def compileDir(dirName='.', backupServletFiles=True):
    """Compile all the Cheetah files in a directory."""
    
    cheetahFiles = glob(dirName + '/*' + CHEETAH_EXTENSION)
    namesMinusExt = [pathSplitext(fileName)[0] for fileName in cheetahFiles] 
    
    if backupServletFiles:
        for i in range(len(namesMinusExt)):
            if exists( namesMinusExt[i] + SERVLET_EXTENSION):
                print 'backing up', namesMinusExt[i] + SERVLET_EXTENSION
                os.rename(namesMinusExt[i] + SERVLET_EXTENSION,
                          namesMinusExt[i] + SERVLET_BACKUP_EXT)

    for name in namesMinusExt:
        compileFile(name)
        
def compileFile(fileNameMinusExt):
    """Compile an single Cheetah file.  """
    
    fp = open(fileNameMinusExt + CHEETAH_EXTENSION)
    templateExt = fp.read()
    fp.close()
    servletName = pathSplit(fileNameMinusExt)[1]
    servletCode = wrapTemplateCode(templateExt, servletName)
    print 'compiled ', fileNameMinusExt + CHEETAH_EXTENSION, 'to', fileNameMinusExt + SERVLET_EXTENSION
     
    fp = open(fileNameMinusExt + SERVLET_EXTENSION,'w')
    fp.write(servletCode)
    fp.close

def recursiveCompile(dir='.', backupServletFiles=True):
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
        compileDir(dir, backupServletFiles=backupServletFiles) 
    
class MainProgram:
    """A command line interface class."""
    
    def run(self):
        """The main program controller."""
        try:
            opts, args = getopt.getopt( sys.argv[1:], 'd:R:', [])

        except getopt.GetoptError:
            # print help information and exit:
            self.usage()
            sys.exit(2)

        if not opts:
            try:
                fileName = args[0]
            except:
                self.usage()
                sys.exit(2)
                
            servletName = pathSplitext(pathSplit(fileName)[1])[0]
            fp = open(fileName)
            templateExt = fp.read()
            fp.close()
            print wrapTemplateCode(templateExt, servletName)

        for o, a in opts:
            if o in ('-h',):
                self.usage()
                sys.exit()
            if o in ('-R',):
                recursiveCompile(a)
                sys.exit()
            if o in ('-d',):
                compileDir(a)
                sys.exit()


    def usage(self):
        print \
"""Cheetah %(version)s Command-Line Compiler by %(author)s

Compiles Cheetah files (.tmpl) into Webware servlet files (.py)

Usage: 
  %(scriptName)s filename   ---> compile 'filename', output to stdout
  %(scriptName)s -h         ---> print this help and exit
  %(scriptName)s -d dir     ---> compile all files in dir, output to new files
  %(scriptName)s -R dir     ---> same as -d, but operates recursively on subdirs
  
""" % {'scriptName':sys.argv[0],
       'version':version,
       'author':'Tavis Rudd',
       }


    
##################################################
## if run from the command line ##
if __name__ == '__main__':

    MainProgram().run()


