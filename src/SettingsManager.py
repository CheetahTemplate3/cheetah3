#!/usr/bin/env python
# $Id: SettingsManager.py,v 1.3 2001/08/02 06:22:14 tavis_rudd Exp $
"""Provides a mixin class for managing settings dictionaries

Meta-Data
==========
Author: Tavis Rudd <tavis@calrudd.com>
Version: $Revision: 1.3 $
Start Date: 2001/05/30
Last Revision Date: $Date: 2001/08/02 06:22:14 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.3 $"[11:-2]


##################################################
## DEPENDENCIES ##

import os.path
from copy import deepcopy, copy
from ConfigParser import ConfigParser
import re
from tokenize import Intnumber, Floatnumber, Number
from types import StringType, IntType, FloatType, LongType, \
     ComplexType, NoneType, UnicodeType, DictType
from cStringIO import StringIO

#intra-package imports ...
from Utilities import mergeNestedDictionaries

##################################################
## CONSTANTS & GLOBALS ##

True = (1==1)
False = (1==0)

numberRE = re.compile(Number)
complexNumberRE = re.compile('[\(]*' +Number + r'[ \t]*\+[ \t]*' + Number + '[\)]*')

convertableToStrTypes = (StringType, IntType, FloatType,
                         LongType, ComplexType, NoneType,
                         UnicodeType)

##################################################
## FUNCTIONS ##

def stringIsNumber(theString):
    """Return True if theString represents a Python number, False otherwise.
    This also works for complex numbers."""
    match = complexNumberRE.match(theString)
    if not match:
        match = numberRE.match(theString)
    if not match or (match.end() != len(theString)):
        return False
    else:
        return True
        
def convStringToNum(theString):
    """Convert a string representation of a Python number to the Python version"""
    if not stringIsNumber(theString):
        raise Error(theString + ' cannot be converted to a Python number')
    return eval(theString)

##################################################
## CLASSES ##

class Error(Exception):
    pass

class NoDefault:
    pass

class SettingsManager:
    """A mixin class that provides facilities for managing settings dictionaries.
    """

    _settings = {}
    
    def initializeSettings(self):
        
        """A hook that allows for complex setting initialization sequences that
        involve references to 'self' or other settings.  For example:
              self._settings['myCalcVal'] = self._settings['someVal'] * 15        
        This method should be called by the class' __init__() method when needed.
        
        The dummy implementation should be reimplemented by subclasses.
        """
        pass
    
    def updateSettings(self, newSettings, merge=True):
        """Update the settings with a selective merge or a complete overwrite."""
        if merge:
            self._settings = mergeNestedDictionaries(self._settings, newSettings)
        else:
            self._settings = newSettings

    def updateSettingsFromPythonString(self, theString, merge=True):
        """Update the settings from a code in a text string."""
        nameSpace = {'self':self}
        exec theString in nameSpace
        del nameSpace['self']
        self.updateSettings(nameSpace,
                            merge=nameSpace.get('mergeSettings',merge) )
        
    def updateSettingsFromFile(self, path, merge=True):
        """Update the settings from Python code in text file."""
        path = self.normalizePath(path)
        fp = open(path)
        contents = fp.read()
        fp.close()
        self.updateSettingsFromPythonString(contents, merge=merge)


    def updateSettingsFromIniFile(self, path, **kw):
        """See the docstring for updateSettingsFromIniFileObj"""
        path = self.normalizePath(path)
        fp = open(path)
        self._updateSettingsFromIniFileObj(fp, **kw)
        fp.close()

    def _updateSettingsFromIniFileObj(self, inFile, convert=True, merge=True):
        """Update the settings from a text file using the syntax accepted by
        Python's standard ConfigParser module (like Windows .ini files).

        If the keyword arg 'convert' is True then the strings in the ini file
        that represent numbers or 'True'/'False' will be converted into the
        proper Python types.
        
        The ini format doesn't handle nesting well and has many other
        limitations so it is not the recommended format for config files.  In
        most cases it is better to use standard Python syntax and the
        SettingsManager.updateSettingsFromFile() method."""

        p = ConfigParser()
        p.readfp(inFile)
        sects = p.sections()
        newSettings = {}

        sects = p.sections()
        newSettings = {}
        
        for s in sects:
            newSettings[s] = {}
            for o in p.options(s):
                if o != '__name__':
                    newSettings[s][o] = p.get(s,o)

        ## loop through new settings -> deal with global settings, numbers,
        ## booleans and None

        for sect, subDict in newSettings.items():
            if convert:
                for key, val in subDict.items():
                    if val.lower() == 'none':
                        subDict[key] = None
                    if val.lower() == 'true':
                        subDict[key] = True
                    if val.lower() == 'false':
                        subDict[key] = False
                        
                    if stringIsNumber(val):
                        subDict[key] = convStringToNum(val)
                        
            if sect.lower() == 'global':
                newSettings.update(subDict)
                del newSettings[sect]
                        
        ## Finally, update the settings dict
        self.updateSettings(newSettings,
                            merge=newSettings.get('mergeSettings',merge))
        
    def normalizePath(self, path):
        """A hook for any neccessary path manipulations.

        For example, when this is used with Webware servlets all relative paths
        must be converted so they are relative to the servlet's directory rather
        than relative to the program's current working dir.

        The default implementation just normalizes the path for the current
        operating system."""
        
        return os.path.normpath(path.replace("\\",'/'))

    def setting(self, name, default=NoDefault):
        """Get a setting from self._settings, with or without a default value."""
        if default is NoDefault:
            return self._settings[name]
        else:
            return self._settings.get(name, default)
        
    def setSetting(self, name, value):
        """Set a setting in self._settings."""
        self._settings[name] = value

    def settings(self):
        """Return a reference to the settings dictionary"""
        return self._settings
        
    def copySettings(self):
        """Returns a shallow copy of the settings dictionary"""
        return copy(self._settings)

    def deepcopySettings(self):
        """Returns a deep copy of the settings dictionary"""
        return deepcopy(self._settings)

    def _createIniFile(self, outFile=StringIO()):
        """Write all the settings that can be represented as strings to an .ini
        style config string.

        This method can only handle one level of nesting and will only work with
        numbers, strings, and None."""

        iniSettings = {'globals':{}}
        globals = iniSettings['globals']
        
        for key, theSetting in self.settings().items():
            if type(theSetting) in convertableToStrTypes:
                globals[key] = theSetting
            if type(theSetting) is DictType:
                iniSettings[key] = {}
                for subKey, subSetting in theSetting.items():
                    if type(subSetting) in convertableToStrTypes:
                        iniSettings[key][subKey] = subSetting

        outFileWrite = outFile.write
        for section in iniSettings.keys():
            outFileWrite("[" + section + "]\n")
            sectDict = iniSettings[section]
            for (key, value) in sectDict.items():
                if key == "__name__":
                    continue
                outFileWrite("%s = %s\n" % (key, value))
            outFileWrite("\n")

        return outFile
        
    def writeIniFile(self, path):
        """Write all the settings that can be represented as strings to an .ini
        style config file."""
        
        path = self.normalizePath(path)
        fp = open(path,'w')
        self._createIniFile(fp)
        fp.close()
        
    def getIniString(self):
        """Return a string with the settings in .ini file format."""
        
        return self._createIniFile().getvalue()
 
