#!/usr/bin/env python
# $Id: SettingsManager.py,v 1.1 2001/06/13 03:50:40 tavis_rudd Exp $
"""Provides a mixin class for managing settings dictionaries

Meta-Data
==========
Author: Tavis Rudd <tavis@calrudd.com>
Version: $Revision: 1.1 $
Start Date: 2001/05/30
Last Revision Date: $Date: 2001/06/13 03:50:40 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.1 $"[11:-2]


##################################################
## DEPENDENCIES ##

from copy import deepcopy, copy

#intra-package imports ...
from Utilities import mergeNestedDictionaries

##################################################
## CONSTANTS & GLOBALS ##

True = (1==1)
False = (1==0)


##################################################
## CLASSES ##

class Error(Exception):
    pass

class NoDefault:
    pass

class SettingsManager:
    """A mixin class that provides facilities for managing settings dictionaries."""

    def initializeSettings(self):
        """This dummy method should be reimplemented by subclasses."""
        self._settings = {}
    
    def updateSettings(self, newSettings, merge=True):
        """Update the settings with a selective merge or a complete overwrite."""
        if merge:
            self._settings = mergeNestedDictionaries(self._settings, newSettings)
        else:
            self._settings = newSettings

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
   
