#!/usr/bin/env python
# $Id: Debugger.py,v 1.1 2001/06/13 03:50:40 tavis_rudd Exp $
"""Debugging tools for the TemplateServer package

THIS FILE IS NOT READY FOR USE!!
It was created for an earlier version of TemplateServer and has not been updated yet.

Meta-Data
==========
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.1 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2001/06/13 03:50:40 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.1 $"[11:-2]



##################################################
## DEPENDENCIES ##
import time
from TemplateServer.Version import version

##################################################
## CONSTANTS & GLOBALS ##

True = (1==1)
False = (0==1)
currentTime = time.time                 # used in the cache refresh code


##################################################
## FUNCTIONS ##


## methods for obtaining meta-information about the template being servered ##

def _tags(server, removeDuplicates=True):
    """return a list of all TemplateServer tags in the template."""
    tags = server._settings['internalDelims']['placeholderRE'].findall(server._internalTemplate)

    if removeDuplicates:
        tags = removeDuplicateValues(tags)

    tokens = []
    tagsList = {}
    
    for tag in tags:
        token, tag = tag.split(server._settings['codeGenerator']['tagTokenSeparator'])
        if tagsList.has_key(token):
            tagsList[token].append(tag)
        else:
            tagsList[token] = [tag,]
        
    return tagsList

def _names(server, removeDuplicates=True):
    """return a list of all the NameMapper vars embedded in the template."""
    names = server._tags()['nameMapper']
    
    if removeDuplicates:
        names = removeDuplicateValues(names)
    return names 

def _cachedNames(server):
    """return a list of all NameMapper vars in the template that are cached"""
    names = [name for name in filter(lambda name: name.find('*')!=-1 , server._names()) ]
    return names 

def _uncachedNames(server):
    """return a list of all NameMapper vars in the template that aren't cached"""
    names = filter(lambda name: name.find('*')==-1 , server._names())
    return names 


## methods to handle command-line usage ##

def runAsMainProgram(server):
    """Enables the template to function as a standalone command-line program for
    static page generation and testing/debugging"""
    
    import getopt, sys
    from pprint import pprint
    
    try:
        opts, args = getopt.getopt(
            sys.argv[1:], 'horiptnvdV', ['output','raw','afterParsedIncludes','afterIncludes',
                                         'internalTemplate',
                                         'pythonCode','tags','names','cached','uncached',
                                         'allnames','values','doc','help','version'])
    except getopt.GetoptError:
        # print help information and exit:
            server._TemplateServerUsage()
            sys.exit(2)
    if not opts:
        print server
        
    for o, a in opts:
        if o in ('-h', '--help'):
            server._TemplateServerUsage()
            
        if o in ('-o', '--output'):
            print server
        if o in ('-r','--raw'):
            print server._rawTemplate
        if o in ('--afterParsedIncludes',):
            print server._rawTemplateAfterParsedIncludes
        if o in ('-i','--afterIncludes'):
            print server._rawTemplateAfterPlainIncludes

        if o in ('--internalTemplate',):
            print server._internalTemplate

        if o in ('-p','--pythonCode'):
            print server._templateFunctionDef
            
        if o in ('-t','--tags'):
            #pprint( server._names() )
            pprint( server._tags() )
            
        if o in ('-n','--names'):
            #pprint( server._names() )
            pprint( server._tags()['nameMapper'] )
        if o in ('--cached',):
            pprint( server._cachedNames() )
        if o in ('--uncached',):
            pprint( server._uncachedNames() )
        if o in ('--allnames',):
            pprint( server._names(removeDuplicates=False) )

        if o in ('-v','--values',):
            
            print "="*80
            print "staticValuesCache (all names prefixed with *)"
            print "="*80
            print
            pprint( server._staticValuesCache )
            print

            print "="*80
            print "callableNamesCache (all names that map to methods, functions, etc.)"
            print "="*80
            print
            pprint( server._callableNamesCache )
            print

            print "="*80
            print "pluginsCache (all names that map to TemplatServer plugins)"
            print "="*80
            print
            pprint( server._plugins )
            print

            print "="*80
            print "nestedTemplatesCache (all names that map to other templates)"
            print "="*80
            print
            pprint( server._nestedTemplatesCache )
            print

            print "="*80
            print "timedRefreshList (all cached vars that are scheduled for an update)"
            print "="*80
            print "current time in epoch seconds:", currentTime()
            print
            print "name,  nextUpdateTime(secs-since-epoch),  updateInterval(minutes)"
            print "-"*80
            pprint( server._timedRefreshList )
            print
                           
        if o in ('-d','--doc'):
            import os
            os.system('pydoc ./' + server.__filename__)
        if o in ('-V', '--version'):
            print version


def _TemplateServerUsage():
    """Print the TemplateServer command line usage information."""
    print \
"""Usage: python %(scriptName)s [OPTIONS]

TemplateServer %(version)s by %(author)s

  -h, --help      print this help and exit

  -o, --output    print the template's default output
  -r, --raw       print the raw template after processing the includes
  -b, --beforeIncludes
                  print the raw template before processing the includes
  -i, --internal  print template's tranlation to the internal delimeters and exit
  -p, --pythonCode print template's tranlation to python code and exit

  The following options show the variable names embedded in the
  template with their original order maintained.
  ---------------------------------------------------------------
  -t, --tags      print a list of all the tags in the template, grouped by type
  
  -n, --names     print a list of the variable names in the template
                  Names prefixed with * are statically cached.
      --cached    print a list of the cached variable names
      --uncached  print a list of the uncached variable names
      --allnames  same as names, but shows duplicates
      
  -v  --values    print data stored internally in the cache dictionaries/lists:
                  *staticValuesCache 
                  *callableNamesCache 
                  *nestedTemplatesCache
                  *timedRefreshList
     
  -d, --doc       display the templates documentation using pydoc
                  The author must have set the Template's
                  __filename__ attribute for this to work.
                  If this is not set, the docs for the last base class that
                  did set this attribute will be shown instead.
                  > pydoc ./THISFILENAME does the same thing.
                  
  -V, --version   print version information

""" % {'scriptName':sys.argv[0],
       'version':version,
       'author':'Tavis Rudd',
       }
