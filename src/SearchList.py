#!/usr/bin/env python
# $Id: SearchList.py,v 1.1 2001/06/18 17:44:12 tavis_rudd Exp $

"""Provides a SearchList class for Cheetah Template Objects.  The searchList is
used to store the list of namespaces to map $placeholder values from.

Meta-Data
================================================================================
Authors: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution
         under the terms of the Python license.
Version: $Revision: 1.1 $
Start Date: 2001/04/03
Last Revision Date: $Date: 2001/06/18 17:44:12 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.1 $"[11:-2]

##################################################
## DEPENDENCIES ##

from UserList import UserList
from types import StringType
#intra-package imports ...
from NameMapper import valueForName, \
     hasName, \
     hasKey, \
     translateNameToCode, \
     NotFound

##################################################
## GLOBALS AND CONSTANTS ##

True = (1==1)
False = (0==1)

##################################################
## CLASSES ##

class Error(Exception):
    pass

class SearchList(UserList):
    def get(self, name):
        for namespace in self.data:
            try:
                val = valueForName(namespace, name)
                return val
            except NotFound:
                pass           
        raise NotFound
    
    def translateName(self, name):
        if type(name)==StringType:
            nameChunks=name.split('.')
        else:
            nameChunks = name
        
        namespaceNum = None
        for i in range(len(self)):
            
            if hasKey(self[i], nameChunks[0]):
                namespaceNum = i
                break

        if namespaceNum == None:
            raise NotFound

        return '[' + str(namespaceNum) + ']' + translateNameToCode(
            self[namespaceNum], nameChunks)
        
            
