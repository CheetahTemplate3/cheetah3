#!/usr/bin/env python
# $Id: DataDirective.py,v 1.2 2001/08/15 17:49:51 tavis_rudd Exp $
"""DataDirective Processor class Cheetah's codeGenerator

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.2 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/08/15 17:49:51 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.2 $"[11:-2]

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
        gobbleWS = re.compile(bits['start_gobbleWS'] + r'data[\t ]*(?P<args>.*?)' +
                              bits['endGrp'] +
                              r'(?P<contents>.*?)' +
                              bits['startTokenEsc'] + r'end data[\t ]*' +
                              bits['endGrp'],
                              re.DOTALL | re.MULTILINE)

        plain = re.compile(bits['start'] + r'data[\t ]*(?P<args>.*?)' +
                           bits['endGrp'] +
                           r'(?P<contents>.*?)' +
                           bits['startTokenEsc'] + r'end data[\t ]*' +
                           bits['endGrp'],
                           re.DOTALL | re.MULTILINE)


        self._delimRegexs = [gobbleWS, plain]
        
    def preProcess(self, templateDef):
        templateObj = self.templateObj
        
        def dataDirectiveProcessor(match, self=self, templateObj=templateObj):
            """process any #data directives that are found in the template
            extension"""
            
            args = match.group('args').split(',')
            contents = match.group('contents')
            
            newDataDict = {'self':templateObj}
            exec contents in {}, newDataDict
    
            del newDataDict['self']
            if not 'nomerge' in args:
                self.mergeNewTemplateData(newDataDict)
            else:
                for key, val in newDataDict.items():
                    setattr(templateObj,key,val)
                
            return '' # strip the directive from the extension
    
        for RE in self._delimRegexs:
            templateDef = RE.sub(dataDirectiveProcessor, templateDef)
        return templateDef
