#!/usr/bin/env python
# $Id: SettingsManager.py,v 1.16 2001/12/19 02:10:25 tavis_rudd Exp $
"""Provides a mixin/base class for managing application settings 

Meta-Data
==========
Author: Tavis Rudd <tavis@calrudd.com>
Version: $Revision: 1.16 $
Start Date: 2001/05/30
Last Revision Date: $Date: 2001/12/19 02:10:25 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__revision__ = "$Revision: 1.16 $"[11:-2]


##################################################
## DEPENDENCIES ##

import sys
import os.path
from copy import deepcopy, copy
from ConfigParser import ConfigParser 
import re
from tokenize import Intnumber, \
     Floatnumber, \
     Number
from types import StringType, \
     IntType, \
     FloatType, \
     LongType, \
     ComplexType, \
     NoneType, \
     UnicodeType, \
     DictType
import types

try:
    from StringIO import StringIO
except:
    from cStringIO import StringIO

import imp                 # used by SettingsManager.updateSettingsFromPySrcFile()

try:
    import threading
    from threading import Lock  # used for thread lock on sys.path manipulations
except:
    ## provide a dummy for non-threading Python systems
    class Lock:
        def acquire(self):
            pass
        def release(self):
            pass

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

def mergeNestedDictionaries(dict1, dict2):
    """Recursively merge the values of dict2 into dict1.

    This little function is very handy for selectively overriding settings in a
    settings dictionary that has a nested structure.  """
    
    for key,val in dict2.items():
        if dict1.has_key(key) and type(val) == types.DictType and \
           type(dict1[key]) == types.DictType:
            
            dict1[key] = mergeNestedDictionaries(dict1[key], val)
        else:
            dict1[key] = val
    return dict1
    
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
    """Convert a string representation of a Python number to the Python Version"""
    if not stringIsNumber(theString):
        raise Error(theString + ' cannot be converted to a Python number')
    return eval(theString, {}, {})

##################################################
## CLASSES ##

class Error(Exception):
    pass

class NoDefault:
    pass

class ConfigParserCaseSensitive(ConfigParser):
    """A case sensitive Version of the standard Python ConfigParser."""
    def optionxform(self, optionstr):
        return optionstr

class SettingsManager:
    """A mixin class that provides facilities for managing application settings.
    
    SettingsManager is designed to:
    - work well with nested settings dictionaries of any depth
    - be able to read/write .ini style config files (or strings)
    - be able to read settings from Python src files (or strings) so that
      complex Python objects can be stored in the application's settings
      dictionary.  For example, you might want to store references to various
      classes that are used by the application and plugins to the application
      might want to substitute one class for another.
    - allow sections in .ini config files to be extended by settings in Python
      src files
    - allow python literals to be used values in .ini config files
    - maintain the case of setting names, unlike the ConfigParser module

    This method must be called by subclasses.
    """

    _sysPathLock = Lock()   # used by the updateSettingsFromPySrcFile() method

    _ConfigParserClass = ConfigParserCaseSensitive #incase __init__ isn't called
    
    def __init__(self, caseSensitive=True):
        self._settings = {}
        if caseSensitive:
            self.setConfigParserClass(ConfigParserCaseSensitive)
        else:
            self.setConfigParserClass(ConfigParser)

    def setConfigParserClass(self, klass):
        self._ConfigParserClass = klass
        
    def _initializeSettings(self):
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
            mergeNestedDictionaries(self._settings, newSettings)
        else:
            self._settings.update(newSettings)

    def updateSettingsFromPySrcStr(self, theString, merge=True):
        """Update the settings from a code in a Python src string."""
        newSettings = self.readSettingsFromPySrcStr(theString)
        self.updateSettings(newSettings,
                            merge=newSettings.get('mergeSettings',merge) )
        
    def updateSettingsFromPySrcFile(self, path, merge=True):
        """Update the settings from variables in a Python source file.

        This method will temporarily add the directory of src file to sys.path so
        that import statements relative to that dir will work properly."""
        newSettings = self.readSettingsFromPySrcFile(path)
        self.updateSettings(newSettings,
                            merge=newSettings.get('mergeSettings',merge) )

    def readSettingsFromPySrcFile(self, path):
        """Return new settings dict from variables in a Python source file.

        This method will temporarily add the directory of src file to sys.path so
        that import statements relative to that dir will work properly."""
        
        path = self.normalizePath(path)
        dirName = os.path.dirname(path)

        self._sysPathLock.acquire()
        sys.path.insert(0, dirName)

        # I'm not doing this using execfile on purpose!
        fp = open(path)
        pySrc = fp.read()
        fp.close()
        newSettings = self.readSettingsFromPySrcStr(pySrc)
        
        if sys.path[0] == path:   # it might have modified by another thread
            del sys.path[0]
        self._sysPathLock.release()

        return newSettings
        
    def readSettingsFromPySrcStr(self, theString):
        """Return a dictionary of the settings in a Python src string."""
        newSettings = {'self':self}
        exec theString in {}, newSettings
        del newSettings['self']
        return newSettings

    def updateSettingsFromConfigFile(self, path, **kw):
        
        """Update the settings from a text file using the syntax accepted by
        Python's standard ConfigParser module (like Windows .ini files). NOTE:
        this method maintains case unlike the ConfigParser module, unless this
        class was initialized with the 'caseSensitive' keyword set to False.

        All setting values are initially parsed as strings. However, If the
        'convert' arg is True this method will do the following value
        conversions:
        
        * all Python numeric literals will be coverted from string to number
        
        * The string 'None' will be converted to the Python value None
        
        * The string 'True' will be converted to a Python truth value
        
        * The string 'False' will be converted to a Python false value
        
        * Any string starting with 'python:' will be treated as a Python literal
          or expression that needs to be eval'd. This approach is useful for
          declaring lists and dictionaries.

        If a config section titled 'Globals' is present the options defined
        under it will be treated as top-level settings.
        """
        
        path = self.normalizePath(path)
        fp = open(path)
        self.updateSettingsFromConfigFileObj(fp, **kw)
        fp.close()

    def readSettingsFromConfigFile(self, path, convert=True):
        path = self.normalizePath(path)
        fp = open(path)
        settings = self.readSettingsFromConfigFileObj(fp, convert=convert)
        fp.close()
        return settings
    
    def updateSettingsFromConfigFileObj(self, inFile, convert=True, merge=True):
        
        """See the docstring for .updateSettingsFromConfigFile()

        The caller of this method is responsible for closing the inFile file
        object."""

        newSettings = self.readSettingsFromConfigFileObj(inFile, convert=convert)
        self.updateSettings(newSettings,
                            merge=newSettings.get('mergeSettings',merge))

    def updateSettingsFromConfigStr(self, configStr, convert=True, merge=True):
        
        """See the docstring for .updateSettingsFromConfigFile()

        The caller of this method is responsible for closing the inFile file
        object."""

        configStr = '[globals]\n' + configStr
        inFile = StringIO(configStr)
        newSettings = self.readSettingsFromConfigFileObj(inFile, convert=convert)
        self.updateSettings(newSettings,
                            merge=newSettings.get('mergeSettings',merge))

    def readSettingsFromConfigFileObj(self, inFile, convert=True):
        """Return the settings from a config file that uses the syntax accepted by
        Python's standard ConfigParser module (like Windows .ini files).

        See .updateSettingsFromConfigFile() for more information.
        """
        
        p = self._ConfigParserClass()
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
        ## booleans and None ++ also deal with 'importSettings' commands

        for sect, subDict in newSettings.items():
            for key, val in subDict.items():
                if convert:
                    if val.lower().startswith('python:'):
                        subDict[key] = eval(val[7:],{},{})
                    if val.lower() == 'none':
                        subDict[key] = None
                    if val.lower() == 'true':
                        subDict[key] = True
                    if val.lower() == 'false':
                        subDict[key] = False
                    if stringIsNumber(val):
                        subDict[key] = convStringToNum(val)
                        
                ## now deal with any 'importSettings' commands
                if key.lower() == 'importsettings':
                    if val.find(';') < 0:
                        importedSettings = self.readSettingsFromPySrcFile(val)
                    else:
                        path = val.split(';')[0]
                        rest = ''.join(val.split(';')[1:]).strip()
                        parentDict = self.readSettingsFromPySrcFile(path)
                        importedSettings = eval('parentDict["' + rest + '"]')
                        
                    subDict.update(mergeNestedDictionaries(subDict,
                                                           importedSettings))
                        
            if sect.lower() == 'globals':
                newSettings.update(newSettings[sect])
                del newSettings[sect]
                
        return newSettings
    
    def normalizePath(self, path):
        """A hook for any neccessary path manipulations.

        For example, when this is used with WebKit servlets all relative paths
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

    def _createConfigFile(self, outFile=StringIO()):
        """Write all the settings that can be represented as strings to an .ini
        style config string.

        This method can only handle one level of nesting and will only work with
        numbers, strings, and None."""

        iniSettings = {'Globals':{}}
        globals = iniSettings['Globals']
        
        for key, theSetting in self.settings().items():
            if type(theSetting) in convertableToStrTypes:
                globals[key] = theSetting
            if type(theSetting) is DictType:
                iniSettings[key] = {}
                for subKey, subSetting in theSetting.items():
                    if type(subSetting) in convertableToStrTypes:
                        iniSettings[key][subKey] = subSetting
        
        sections = iniSettings.keys()
        sections.sort()
        outFileWrite = outFile.write # short-cut namebinding for efficiency
        for section in sections:
            outFileWrite("[" + section + "]\n")
            sectDict = iniSettings[section]
            
            keys = sectDict.keys()
            keys.sort()
            for key in keys:
                if key == "__name__":
                    continue
                outFileWrite("%s = %s\n" % (key, sectDict[key]))
            outFileWrite("\n")

        return outFile
        
    def writeConfigFile(self, path):
        """Write all the settings that can be represented as strings to an .ini
        style config file."""
        
        path = self.normalizePath(path)
        fp = open(path,'w')
        self._createConfigFile(fp)
        fp.close()
        
    def getConfigString(self):
        """Return a string with the settings in .ini file format."""
        
        return self._createConfigFile().getvalue()
