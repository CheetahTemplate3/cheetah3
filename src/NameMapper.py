#!/usr/bin/env python
# $Id: NameMapper.py,v 1.9 2001/08/12 20:12:34 tavis_rudd Exp $

"""Utilities for accessing the members of an object via string representations
of those members.  Template processing is its primary intended use.

Description
================================================================================

This module is similar to Webware's NamedValueAccess, but with the following
basic differences:

- you don't need to inherit the NamedValueAccess mixin to use it

- the functionality of NamedValueAccess was abstracted into two standalone
  functions: valueForName() and valueForKey().  valueForName() is recursive and
  relies on valueForKey.

- the mappings aren't cached in this version.  We are investigating ways of
  caching mappings for mutatible objects only.

- any mapping object or object that works with python's getattr() builtin
  function can be searched (classes, instances, dictionaries, btrees?, etc.),
  therefore locals(), globals(), and __builtins__ all work

- NamedValueAccess only works with methods.  NameMapper works with any callable
  object, such as plain functions or classes.

- if a name maps to a callable object (function, method, class, etc.)
  valueForName returns a reference to the object is returned instead of the
  object's return value.  The caller is responsible for dealing with it. This
  allows the caller to cache the reference and execute it when ever needed.

and some extra features:

- nested objects can be descended into, for any depth, so long as nested objects
  are dicts or work with getattr().  NamedValueAccess was limited to ojects that
  inherited the NamedValueAccess mixin.

Like NamedValueAccess:

- you can provide a default value to substitute for names that can't be found.
  If you don't provide a default and the name can't be found the exception
  NameMapper.NotFound will be raised. This is similar to the .get() method of
  dictionaries.


Usage
================================================================================
This module is not safe for 'from NameMapper import *'!

See the example at the bottom of this file.
The Cheetah package implements a less trivial example.

Meta-Data
================================================================================
Authors: Tavis Rudd <tavis@calrudd.com>,
         Chuck Esterbrook <echuck@mindspring.com>
License: This software is released for unlimited distribution
         under the terms of the Python license.
Version: $Revision: 1.9 $
Start Date: 2001/04/03
Last Revision Date: $Date: 2001/08/12 20:12:34 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>," +\
             "\nChuck Esterbrook <echuck@mindspring.com>"
__version__ = "$Revision: 1.9 $"[11:-2]

##################################################
## DEPENDENCIES ##

import types
from types import StringType, InstanceType, ClassType 
import re
# it uses the string methods and list comprehensions added in recent versions of python

##################################################
## GLOBALS AND CONSTANTS ##

True = (1==1)
False = (0==1)

class NoDefault:
    pass

##################################################
## FUNCTIONS ##

try:
    from _namemapper import NotFound, valueForKey, valueForName, valueFromSearchList
    # it is possible, with Jython for example, that _namemapper.c hasn't been compiled
except:
    class NotFound(Exception):
        pass
    
    def valueForKey(obj, key):
    
        """Get the value of the specified key.  The 'obj' can be a a mapping or any
        Python object that supports the __getattr__ method. The key can be a mapping
        item, an attribute or an underscored attribute."""
    
        if hasattr(obj, key):
            return getattr(obj, key)
        try:
            return obj[key]
        except:
            if hasattr(obj, '_' + key):
                return getattr(obj, '_' + key)
            else:
                raise NotFound, key


    def valueForName(obj, name, executeCallables=False):
        """Get the value for the specified name.  This function can be called
        recursively.  """
    
        if type(name)==StringType:
            # then this is the first call to this function.
            nameChunks=name.split('.')
        else:
            #if this function calls itself then name already is a list of nameChunks
            nameChunks = name
            
        return _valueForName(obj, nameChunks, executeCallables=executeCallables)
    
    def _valueForName(obj, nameChunks, executeCallables=False):
        ## go get a binding for the key ##
        firstKey = nameChunks[0]
        binding = valueForKey(obj, firstKey)
        if executeCallables and callable(binding) and \
           type(binding) not in (InstanceType, ClassType):
            # the type check allows access to the methods of instances
            # of classes with __call__() defined
            # and also allows obj.__class__.__name__
            binding = binding()
    
        if len(nameChunks) > 1:
            # its a composite name like: nestedObject.item
            return _valueForName(binding, nameChunks[1:],
                                executeCallables=executeCallables)
        else:
            # its a single key like: nestedObject
            return binding

    def valueFromSearchList(searchList, name, executeCallables=False):
        if type(name)==StringType:
            # then this is the first call to this function.
            nameChunks=name.split('.')
        else:
            #if this function calls itself then name already is a list of nameChunks
            nameChunks = name

        for namespace in searchList:
            try:
                val = _valueForName(namespace, nameChunks, executeCallables=executeCallables)
                return val
            except NotFound:
                pass           
        raise NotFound(name)



##################################################
    
PLAIN_ATTRIBUTE = 0
UNDERSCORED_ATTRIBUTE = 1
MAPPING_KEY = 2

def determineKeyType(obj, key):
    """Determine what type of key 'key' is to 'obj': PLAIN_ATTRIBUTE,
    UNDERSCORED_ATTRIBUTE or MAPPING_KEY.

    Raises NotFound exception if the obj doesn't have the key."""

    if hasattr(obj, key):
        return PLAIN_ATTRIBUTE
    elif hasattr(obj, '_' + key):
        return UNDERSCORED_ATTRIBUTE
    elif hasattr(obj,'has_key') and obj.has_key(key):
        return MAPPING_KEY
    raise NotFound, key

def hasKey(obj, key):
    """Determine if 'obj' has 'key' """
    if hasattr(obj, key):
        return True
    elif hasattr(obj, '_' + key):
        return True
    elif hasattr(obj,'has_key') and obj.has_key(key):
        return True
    return False

def hasName(obj, name):
    """Determine if 'obj' has the 'name' """
    try:
        valueForName(obj, name)
        return True
    except NotFound:
        return False


def translateNameToCode(obj, name, executeCallables=True):
    """Translate a namemapper name to Python code."""
    if type(name)==StringType:
        nameChunks=name.split('.')
    else:
        nameChunks = name

    codeChunks = []
    for name in nameChunks:
        lastItem = eval('obj' + ''.join(codeChunks))
        keyType = determineKeyType(lastItem, name)
        if keyType == PLAIN_ATTRIBUTE:
            code = '.' + name
        if keyType == UNDERSCORED_ATTRIBUTE:
            code = '._' + name
        if keyType == MAPPING_KEY:
            code = '["' + name + '"]'

        currentItem = eval('obj' + ''.join(codeChunks) + code)
        if executeCallables and callable(currentItem) and \
           type(currentItem) not in (InstanceType, ClassType):
            code = code + '()'
            
        codeChunks.append(code)

    return ''.join(codeChunks)


##################################################
## CLASSES ##

class Mixin:
    """@@ document me"""
    def valueForName(self, name):
        return valueForName(self, name)

    def valueForKey(self, key):
        return valueForKey(self, key)

##################################################
## TEST ROUTINES ##
def test():
    import NameMapper.Tests
    NameMapper.Tests.run_tests()

##################################################
## if run from the command line ##

def example():
    class A(Mixin):
        classVar = 'classVar val'
        def method(self,arg='method 1 default arg'):
            return arg

        def method2(self, arg='meth 2 default arg'):
            return {'item1':arg}

        def method3(self, arg='meth 3 default'):
            return arg

    class B(A):
        classBvar = 'classBvar val'
        _underScoreVar = '_underScoreVar val'

        def _underScoreMethod(self):
            return '_underScoreMethod output'

    a = A()
    a.one = 'valueForOne'
    def function(whichOne='default'):
        values = {
            'default': 'default output',
            'one': 'output option one',
            'two': 'output option two'
            }
        return values[whichOne]

    a.dic = {
        'func': function,
        'method': a.method3,
        'item': 'itemval',
        'subDict': {'nestedMethod':a.method3}
        }
    b = 'this is local b'

    alist = ['item0','item1','item2']

    print valueForKey(a.dic,'subDict','NotFound')
    print valueForName(a, 'dic.item','NotFound')
    print valueForName(vars(), 'b','NotFound')
    print valueForName(__builtins__, 'dir','NotFound')()
    print valueForName(vars(), 'a.classVar','NotFound')
    print valueForName(vars(), 'B.underScoreVar','NotFound')
    print valueForName(vars(), 'a.dic.func','NotFound')
    print valueForName(vars(), 'a.method2.item1','NotFound')
    print valueForName(vars(), 'alist.0','NotFound')

if __name__ == '__main__':
    example()



