#!/usr/bin/env python
# $Id: Compiler.py,v 1.6 2001/08/30 04:45:14 hierro Exp $
"""A command line compiler for turning Cheetah files (.tmpl) into Webware
servlet files (.py).

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.6 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2001/08/30 04:45:14 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.6 $"[11:-2]

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
from Version import version

##################################################
## GLOBALS & CONTANTS ##

True = (1==1)
False = (1==0)

CHEETAH_EXTENSION = '.tmpl'
SERVLET_EXTENSION = '.py'
SERVLET_BACKUP_EXT = '.py_bak'
GEN_EXTENSION = 'Gen'



escCharLookBehind = r'(?:(?<=\A)|(?<!\\))'
tagClosure = r'(?:/#|\r\n|\n|\r)'
lazyTagClosure = r'(?:\r\n|\n|\r)'
extendDirectiveRE = re.compile(escCharLookBehind +
                               r'#extend[\f\t ]+(?P<parent>.*?)' +
                               r'[\f\t ]*' + tagClosure, re.DOTALL)

                    
##################################################
## FUNCTIONS ##
    
def wrapTemplateCode(templateExt, name, appendGen=False):
    """Wrap a template definition string in the boiler-plate code needed to create a
    Webware servlet."""

    if appendGen: gen_ext = GEN_EXTENSION
    else: gen_ext = ''
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

class %(name)s%(gen_ext)s(%(parentServlet)s):
    def initializeTemplate(self):
        %(parentServlet)s.initializeTemplate(self)
        self.extendTemplate(templateExt)

""" %  {'parentModule': parentTemplate,
        'parentServlet': parentServlet,
        'name': name,
        'gen_ext': gen_ext,
        }
    else:
        servletCode = "templateExt = r'''" + templateExt
        servletCode += """'''
from Cheetah.Servlet import TemplateServlet

class %(name)s%(gen_ext)s(TemplateServlet):
    def __init__(self):
        TemplateServlet.__init__(self, template=templateExt)

""" % {'name': name,
       'gen_ext': gen_ext,
       }

    return servletCode


def inheritServletCode(filenameMinusExt):
    return '''from %(name)s%(gen_ext)s import %(name)s%(gen_ext)s

class %(name)s(%(name)s%(gen_ext)s):
    pass
''' % {'name': os.path.basename(filenameMinusExt),
       'gen_ext': GEN_EXTENSION,
       }

def compileDir(dirName='.', backupServletFiles=True, appendGen=False):
    """Compile all the Cheetah files in a directory."""
    
    cheetahFiles = glob(dirName + '/*' + CHEETAH_EXTENSION)
    namesMinusExt = [pathSplitext(fileName)[0] for fileName in cheetahFiles] 

    if appendGen:
        gen_ext = GEN_EXTENSION
    else:
        gen_ext = ""
    if backupServletFiles:
        for i in range(len(namesMinusExt)):
            if exists( namesMinusExt[i] + gen_ext + SERVLET_EXTENSION):
                print 'backing up', namesMinusExt[i] + gen_ext + \
                      SERVLET_EXTENSION
                os.rename(namesMinusExt[i] + gen_ext + SERVLET_EXTENSION,
                          namesMinusExt[i] + gen_ext + SERVLET_BACKUP_EXT)

    for name in namesMinusExt:
        compileFile(name, appendGen=appendGen)
        
def compileFile(fileNameMinusExt, appendGen=False):
    """Compile an single Cheetah file.  """
    
    if appendGen: gen_ext = GEN_EXTENSION
    else: gen_ext = ''

    fp = open(fileNameMinusExt + CHEETAH_EXTENSION)
    templateExt = fp.read()
    fp.close()
    servletName = pathSplit(fileNameMinusExt)[1]
    servletCode = wrapTemplateCode(templateExt, servletName,
                                   appendGen=appendGen)
    print 'compiled ', fileNameMinusExt + CHEETAH_EXTENSION, 'to', fileNameMinusExt + gen_ext + SERVLET_EXTENSION
     
    fp = open(fileNameMinusExt + gen_ext + SERVLET_EXTENSION,'w')
    fp.write("""## This module was compiled from
##   %(name)s%(CHEETAH_EXTENSION)s
""" % {"name": fileNameMinusExt, "CHEETAH_EXTENSION": CHEETAH_EXTENSION})
    if appendGen:
        fp.write("""## You should not make changes to this file.  Instead, you should make
## changes to the file %(name)s.py, which will not be overwritten on recompile.
""" % {"name": fileNameMinusExt})
    else:
        fp.write("""## If you make changes to this file they will be overwritten if you recompile
## the .tmpl file, and the old version of the file will be in %(name)s.py_bak
""" % {"name": fileNameMinuxExt})
	
    fp.write(servletCode)
    fp.close()

    if appendGen and not os.path.exists(fileNameMinusExt +
                                        SERVLET_EXTENSION):
        code = inheritServletCode(fileNameMinusExt)
        fp = open(fileNameMinusExt + SERVLET_EXTENSION, "w")
        fp.write(code)
        fp.close()


def recursiveCompile(dir='.', backupServletFiles=True, appendGen=False):
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
        compileDir(dir, backupServletFiles=backupServletFiles,
                   appendGen=appendGen) 
    
class MainProgram:
    """A command line interface class."""
    
    def run(self):
        """The main program controller."""
        try:
            opts, args = getopt.getopt( sys.argv[1:], 'd:R:g', [])

        except getopt.GetoptError, v:
            # print help information and exit:
            print v
            self.usage()
            sys.exit(2)

        setOpts = {}
        for o, a in opts:
            if o in ('-h',):
                self.usage()
                sys.exit()
            if o in ('-R',):
                setOpts['recursiveCompile'] = True
            if o in ('-d',):
                setOpts['compileDir'] = True
            if o in ('-g',):
                setOpts['appendGen'] = True
        if setOpts.has_key('recursiveCompile') and \
           setOpts.has_key('compileDir'):
            self.usage()
            sys.exit()
        if setOpts.has_key('recursiveCompile'):
            recursiveCompile(a, appendGen=setOpts.has_key('appendGen'))
            sys.exit()
        if setOpts.has_key('compileDir'):
            compileDir(a, appendGen=setOpts.has_key('appendGen'))
            sys.exit()
        if not args:
            self.usage()
            sys.exit(2)
        for fileName in args:
            servletName = pathSplitext(pathSplit(fileName)[1])[0]
            fp = open(fileName)
            templateExt = fp.read()
            fp.close()
            print wrapTemplateCode(templateExt, servletName,
                                   appendGen=setOpts.has_key('appendGen'))


    def usage(self):
        print \
"""Cheetah %(version)s Command-Line Compiler by %(author)s

Compiles Cheetah files (.tmpl) into Webware servlet files (.py)

Usage: 
  %(scriptName)s [OPTIONS] filename ---> compile 'filename', output to stdout
  %(scriptName)s -h                 ---> print this help and exit
  %(scriptName)s -d [OPTIONS] dir   ---> compile all files in dir, output to
                                          new files
  %(scriptName)s -R [OPTIONS] dir   ---> same as -d, but operates
                                          recursively on subdirs
  -g                                      Compile to filenameGen.py
  
""" % {'scriptName':os.path.basename(sys.argv[0]),
       'version':version,
       'author':'Tavis Rudd',
       }


    
##################################################
## if run from the command line ##
if __name__ == '__main__':

    MainProgram().run()


