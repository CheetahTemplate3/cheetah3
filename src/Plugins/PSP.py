#!/usr/bin/env python
# $Id: PSP.py,v 1.1 2001/06/13 03:50:40 tavis_rudd Exp $
"""A plugin that allows Cheetah to handle PythonServerPages style coding

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

from Cheetah.Delimeters import delimeters
from Cheetah.Template import EXEC_TAG_TYPE

##################################################
## CONSTANTS & GLOBALS ##

True = (1==1)
False = (0==1)

##################################################
## FUNCTIONS ##


def pythonScriptTagProcessor(templateObj, pythonScript):
    """Process PSP style code that is embedded in the template definition."""

    pythonScript = pythonScript.strip()
    settings = templateObj._settings
    indent = settings['codeGenerator']['indentationStep']
    if not templateObj._codeGeneratorState.has_key('indentLevel'):
        templateObj._codeGeneratorState['indentLevel'] = \
                       settings['codeGenerator']['initialIndentLevel']

    if pythonScript.lower() == 'end': # move out one indent level
        templateObj._codeGeneratorState['indentLevel'] -= 1
        outputCode = indent*templateObj._codeGeneratorState['indentLevel']

    elif pythonScript.lower()[0:4] in ('else','elif') or \
         pythonScript.lower().startswith('except'):
        # continuation of previous block
       
        outputCode = indent*(templateObj._codeGeneratorState['indentLevel']-1) + \
                     pythonScript +"\n" + \
                     indent*templateObj._codeGeneratorState['indentLevel']

    elif pythonScript[len(pythonScript.strip()) -1] == ":":
        # it's the start of a new block
        templateObj._codeGeneratorState['indentLevel'] += 1
        outputCode = indent*(templateObj._codeGeneratorState['indentLevel']-1) + \
                     pythonScript + "\n" + \
                     indent*templateObj._codeGeneratorState['indentLevel']

    elif pythonScript.lower().startswith('='):   # it's a python value eval()
        outputCode = indent*(templateObj._codeGeneratorState['indentLevel']) + \
               "outputList += [str(" + pythonScript[1:] + "),]\n" + \
               indent*templateObj._codeGeneratorState['indentLevel']
    else:                           # it's a chunk of plain python code              
        outputCode = indent*(templateObj._codeGeneratorState['indentLevel']) + \
                     pythonScript + "\n" + \
                     indent*templateObj._codeGeneratorState['indentLevel']

    return outputCode


##################################################
## CLASSES ##

class PSPplugin:
    """A plugin for Cheetah that allows PythonServerPages code (<%...%>,
    <%=...%>) in templates"""
    
    def bindToTemplateServer(self, templateObj):
        """insert the settings neccessary for PSP into the templateObj"""
        pythonScriptSettingsDict = {'type':EXEC_TAG_TYPE,
                                    'processor':pythonScriptTagProcessor,
                                    'delims':[delimeters['<%,%>'], ],
                                    }
        templateObj._settings['codeGenerator']['coreTags']['pythonScript'] = \
                                                    pythonScriptSettingsDict


##################################################
## test from command-line ##
if __name__ == '__main__':
    from Cheetah.Template import Template
    
    templateDef = """
    Testing Cheetah's PSP plugin:

    $testVar
    <% pspVar = 'X' %>
    #set $list = [1,2,3]
    
    #for $i in map(lambda x: x*x*x, $list)
    $i
    <%=self.mapName('testVar')*15%>
    <%for i in range(15):%> <%=i*15%><%=pspVar%><%end%>
    #end for
    """

    print Template(templateDef, {'testVar':1234}, plugins=[PSPplugin()])
        
    
