#!/usr/bin/env python
# $Id: NameMapper.py,v 1.1 2001/06/13 03:50:39 tavis_rudd Exp $

"""Utilities for accessing the members of an object via string representations
of those members.  Template processing is its primary intended use.

Description
================================================================================
@@ add basic desc.

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
The TemplateServer module implements a less trivial example.

Changes
================================================================================
1.10- got rid of the NameMapper class.  There are now two normal functions,
      valueForName and valueForKey, which do all the work.  This brings the core
      down to less than 60 lines of code, and greatly simplifies the interface.

TODO
================================================================================
- write the test cases

Meta-Data
================================================================================
Authors: Tavis Rudd <tavis@calrudd.com>,
         Chuck Esterbrook <echuck@mindspring.com>
License: This software is released for unlimited distribution
         under the terms of the Python license.
Version: $Revision: 1.1 $
Start Date: 2001/04/03
Last Revision Date: $Date: 2001/06/13 03:50:39 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>," +\
             "\nChuck Esterbrook <echuck@mindspring.com>"
__version__ = "$Revision: 1.1 $"[11:-2]

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
digitsRE = re.compile(r'[0-9]+')
isDigit = digitsRE.match
digits = ['0','1','2','3','4','5','6','7','8','9']


class NotFound(Exception):
    pass

class NoDefault:
    pass

##################################################
## FUNCTIONS ##

def valueForName(obj, name, default=NoDefault, exectuteCallables=False):
    """Get the value for the specified name.  This function can be called
    recursively.  """
    
    if type(name)==StringType:
        # then this is the first call to this function.
        nameChunks=name.split('.')
    else:
        #if this function calls itself then name already be a list of nameChunks
        nameChunks = name
        
    ## go get a binding for the key ##
    firstKey = nameChunks[0]
    if len(nameChunks) > 1:
        # its a composite name like: nestedObject.item
        binding = valueForKey(obj, firstKey, default)
        if callable(binding) and type(binding) not in (InstanceType, ClassType):
            # the type check allows access to the methods of instances
            # of classes with __call__() defined
            # and also allows obj.__class__.__name__
            binding = binding()
        
        return valueForName(binding, nameChunks[1:], default,
                            exectuteCallables=exectuteCallables)
    else:
        # its a single key like: nestedObject
        binding =  valueForKey(obj, firstKey, default)
        if exectuteCallables and callable(binding):
            binding = binding()
        return binding



def valueForKey(obj, key, default=NoDefault):
    """Get the value of the specified key.  The key can be a mapping item, an
    attribute or an underscored attribute."""
    
    if hasattr(obj, key):
        binding = getattr(obj, key)
    elif hasattr(obj, '_' + key):
        binding = getattr(obj, '_' + key)
    else: 
        try:
            if key in digits:
                binding = obj[int(key)]    
            else:
                binding = obj.get(key, default)
        except:
            binding = default

    if binding==NoDefault:
        raise NotFound
    else:
        # this is a value or a reference to a callable object
        return binding              


def determineNameType(obj, name):
    """Return the type of a name or raise an exception if it can't be found.

    This function is useful for caching in situations where a caller needs to
    access the a NameMapper-style name repeatedly.  Using this information, the
    name can be translated into a standard python representation by the caller
    on the first request.  Every subsequent request will eval() the python
    representation of the name, with is more efficient than using
    valueForName().

    Names can be of the following types:
    - a 'callable' object.
      In which case we just retrieve a reference of it and call it when needed
    - a 'plain_attribute'
    - an 'underscored_attribute'
    - a 'mapping_key'
    - raise NotFound
    """

    mapping = valueForName(obj,name)
    if callable(mapping):
        return 'callable'
    else:
        nameChunks = name.split('.')
        if len(nameChunks) == 1:
            return determineKeyType(obj, name)
        else:
            numChunks = len(nameChunks)
            return determineKeyType(
                valueForName(obj, "".join(nameChunks[0:numChunks-1])),
                nameChunks[numChunks-1])
        

def determineKeyType(obj, key):
    if hasattr(obj, key):
        if callable(getattr(obj, key)):
            return 'callable'
        else:
            return 'plain_attribute'
    elif hasattr(obj, '_' + key):
        if callable(getattr(obj, '_' + key)):
            return 'callable'
        else:
            return 'underscored_attribute'
    elif hasattr(obj,'has_key'):
        try:
            if callable(obj.get(key)):
                return  'callable'
            else:
                return 'mapping_key'
        except:
            raise NotFound
            


##################################################
## CLASSES ##

class Mixin:
    """@@ document me"""
    def valueForName(self, name, handleArgStrings=False, localsDict=None):
        return valueForName(self, name, handleArgStrings=handleArgStrings,
                            localsDict=localsDict)

    def valueForKey(self, key, handleArgStrings=False, localsDict=None):
        return valueForKey(self, key, handleArgStrings=handleArgStrings,
                            localsDict=localsDict)

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

    print determineNameType(vars(),'B.underScoreVar')
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

 

