#!/usr/bin/env python
# $Id: DataDirective.py,v 1.4 2001/08/16 22:15:17 tavis_rudd Exp $
"""DataDirective Processor class Cheetah's codeGenerator

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.4 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/08/16 22:15:17 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.4 $"[11:-2]

##################################################
## DEPENDENCIES ##

import re

# intra-package imports ...
import TagProcessor

##################################################
## CONSTANTS & GLOBALS ##

True = (1==1)
False = (0==1)

##################################################
## CLASSES ##

class Error(Exception):
    pass

class DataDirective(TagProcessor.TagProcessor):

    def __init__(self, templateObj):
        TagProcessor.TagProcessor.__init__(self,templateObj)

        bits = self._directiveREbits
        reChunk = 'data[\f\t ]*(?P<args>.*?)'
        self._startTagRegexs = self.simpleDirectiveReList(reChunk)
        self._endTagRE = re.compile(bits['start_gobbleWS'] + r'end[\f\t ]+data[\f\t ]*' + 
                              bits['lazyEndGrp'] + '|'+
                              bits['start'] + r'end[\f\t ]+data[\f\t ]*' +
                              bits['endGrp'],
                              re.DOTALL | re.MULTILINE)


    def handleDataDirective(self, startTagMatch, templateDef):
        """process any #data directives that are found in the template
        extension"""

        endTagMatch = self._endTagRE.search(templateDef)
        if not endTagMatch:
            raise Error("Cheetah couldn't find an end tag for the #data directive at\n" +
                        "position " + str(startTagMatch.start()) +
                        " in the template definition.")

        args = startTagMatch.group('args')
        args = args.split(',')
        contents = templateDef[startTagMatch.end() : endTagMatch.start()]

        templateObj = self.templateObj()
        
        newDataDict = {'self':templateObj} 
        exec contents in {}, newDataDict
        del newDataDict['self']
        
        if not 'nomerge' in args:
            templateObj.mergeNewTemplateData(newDataDict)
        else:
            for key, val in newDataDict.items():
                setattr(templateObj,key,val)

        return templateDef[0:startTagMatch.start()] + templateDef[endTagMatch.end():]
        
    def preProcess(self, templateDef):
        for startTagRE in self._startTagRegexs:
            while startTagRE.search(templateDef):
                startTagMatch = startTagRE.search(templateDef)
                templateDef = self.handleDataDirective(startTagMatch=startTagMatch,
                                                       templateDef=templateDef)
        
        return templateDef
