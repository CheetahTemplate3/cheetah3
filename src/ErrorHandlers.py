"""Error Handlers for Cheetah

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.7 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2001/08/16 05:01:37 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.7 $"[11:-2]

##################################################
## DEPENDENCIES ##

import re
import sys
import types
from traceback import format_tb, format_exception


#intra-package imports ...
from Utilities import insertLineNums, getLines, lineNumFromPos
from Version import version

##################################################
## CONSTANTS & GLOBALS ##

True = (1==1)
False = (0==1)

##################################################
## CLASSES ##

class ErrorHandler:
    """An abstract base class for Cheetah ErrorHandlers"""
    
    def __init__(self, templateObj):
        """collect some information about the exception and the server"""
        self._localvars = localvars = sys.exc_traceback.tb_frame.f_locals
        self._templateObj = templateObj
        self._debug = templateObj._settings['debug']

    def format_exc(self):
        return ''.join( format_exception(sys.exc_type, sys.exc_value,
                                         sys.exc_traceback) )
        
    def __str__(self):
        """print the error message"""
        fillValues ={'ver':version,
                     'introText': self.introText(),
                     'debugSettingWarning':self._debugSettingWarning(),
                     'excType':sys.exc_type,
                     'excValue':sys.exc_value,
                     'errorDetails': self.errorDetails(),
                     }
        
        return \
"""================================================================================
                        Cheetah Version %(ver)s

%(introText)s
%(debugSettingWarning)s

Exception Type:   %(excType)s
Exception Value:  %(excValue)s

More information about the error is printed below.  The most general information
from the high-level error handlers is printed first, followed by more specific
information from the lower-level error handlers. A Python traceback is printed
at the very end. There may be some repetition of information.

================================================================================
%(errorDetails)s
""" % fillValues

    def introText(self):
        return ''

    def errorDetails(self):
        return ''   
        
    def _debugSettingWarning(self):
        if not self._debug:
            
            return "\nNOTE: you have Cheetah's debug setting set to " + \
                   "False. Cheetah will\nusually be more helpful " + \
                   "with problems if you set debug to True."
                   
        else:
            return ''

class ResponseErrorHandler(ErrorHandler):
    """An error handler for exceptions raised during the Template serving
    cycle"""
    
    def __init__(self, templateObj):
        ErrorHandler.__init__(self, templateObj)

    def introText(self):
        return """Cheetah compiled this template successfully, but an error (aka Exception)
occurred at run-time when Cheetah was executing the generated code."""
        
    def errorDetails(self):
        msg = self.format_exc()
        msg += "\nHere's a copy of the code that Cheetah generated:\n\n"
        msg += insertLineNums( self._templateObj._generatedCode )
        
        self._templateObj._errorMsgStack.append(msg)
        self._templateObj._errorMsgStack.reverse()
        return '\n'.join( self._templateObj._errorMsgStack )




class CodeGeneratorErrorHandler(ErrorHandler):
    """The master ErrorHandler for Cheetah's codeGenerator."""
    def __init__(self, templateObj):
        ErrorHandler.__init__(self, templateObj)
        self._stage = stage = self._localvars['stage']
        self._stageSettings = templateObj.setting('stages')[stage]

    def introText(self):
        fillValues = {'stage': self._stage,
                     'stageDescription':self._stageSettings['description'],
                     'stageTitle':self._stageSettings['title'],
                     }
        return \
"""An error (aka Exception) occurred during code generation stage %(stage)d.
Stage %(stage)s, '%(stageTitle)s', is when %(stageDescription)s""" % fillValues

    def errorDetails(self):
        self._stageSettings['errorHandler'](self._templateObj)
        self._templateObj._errorMsgStack.reverse()
        return '\n'.join( self._templateObj._errorMsgStack )


class StageErrorHandler(ErrorHandler):
    """ErrorHandler base class for stages of Cheetah's codeGenerator."""
    def __init__(self, templateObj):
        ErrorHandler.__init__(self, templateObj)
        self._templateObj._errorMsgStack.append( self.generateErrMsg() )

    def generateErrMsg(self):
        pass

class Stage1ErrorHandler(StageErrorHandler):
    """ErrorHandler for stage 1 of Cheetah's codeGenerator."""

    def generateErrMsg(self):
        msg = '\n'
        msg += "Cheetah was executing the " + \
               self._localvars['name'] + \
               " preProcessor when the error occurred.\n"
        msg += '-'*80
        return msg
            

class Stage2ErrorHandler(StageErrorHandler):
    """ErrorHandler for stage 2 of Cheetah's codeGenerator."""
    
    def generateErrMsg(self):        
        msg = '\n'
        if self._localvars['subStage'] == 'b':
            msg += "Cheetah was separating tags from the normal text " + \
                      "when the error occurred.\n"
            msg += "This was the state of the template when the error occurred:\n\n"
            msg += insertLineNums( self._localvars['templateDef'] )

        elif self._localvars['subStage'] == 'c':
            msg += "Cheetah was generating code for each of the tags " + \
                      "when the error occurred.\n"
            msg += "This was the textVsTagList being processed:\n\n"
            msg += str( self._localvars['textVsTagsList'] )
            msg += '-'*80
            msg += "\nThis was the state of the template when the error occurred:\n\n"
            msg += insertLineNums( self._localvars['templateDef'] )
            
        elif self._localvars['subStage'] == 'd':
            msg += "Cheetah was joining the code from each of the tags into " + \
                   "a string when the error occurred.\n"
            msg += "This was the list of code chunks (even) and normal text (odd) " + \
                   "being joined:\n\n"
            msg += str( self._localvars['codePiecesFromTextVsTagsList'] )
            msg += '-'*80
            
        return msg


class Stage3ErrorHandler(StageErrorHandler):
    """ErrorHandler for stage 3 of Cheetah's codeGenerator."""

    def generateErrMsg(self):        
        msg = '\n'
        msg += "Cheetah was wrapping the code from the tags up in a " + \
                  "function definition when the error occurred.\n"
        msg += "This was the code from that came from the tag processors:\n\n"
        msg += self._localvars['codeFromTextVsTagsList']
        msg += '-'*80
        return msg


class Stage4ErrorHandler(StageErrorHandler):
    """ErrorHandler for stage 4 of Cheetah's codeGenerator."""

    def generateErrMsg(self):        
        msg = '\n'
        msg += "Cheetah was executing the " + self._localvars['filter'][0] + \
                  " filter when the error occurred.\n"
        msg += "This was the state of the generated when the error occurred:\n\n"
        msg += insertLineNums( self._localvars['generatedCode'] )
        msg += '-'*80
        return msg


class Stage5ErrorHandler(StageErrorHandler):
    """ErrorHandler for stage 5 of Cheetah's codeGenerator."""
    def generateErrMsg(self):        
        generatedCode = self._localvars['generatedCode']
        msg = '\n'
        msg += "Here's a copy of the code that Cheetah generated:\n\n"
        msg += insertLineNums(generatedCode)
        msg += '-'*80
        return msg
