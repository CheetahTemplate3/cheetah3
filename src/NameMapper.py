#!/usr/bin/env python
# $Id: NameMapper.py,v 1.18 2002/05/10 21:20:23 tavis_rudd Exp $

"""This module implements Cheetah's optional NameMapper syntax.

Overview
================================================================================
NameMapper is a simple syntax for accessing Python data structures, functions,
and methods from Cheetah. It's called NameMapper because it 'maps' simple
'names' in Cheetah templates to complex objects in Python.

Its purpose is to make working with Cheetah easy for non-programmers.
Specifically, non-programmers using Cheetah should NOT need to be taught (a)
what the difference is between an object and a dictionary, (b) what functions
and methods are, and (c) what 'self' is.  A further aim (d) is to buffer the
code in Cheetah templates from changes in the implementation of the Python data
structures behind them.

Consider this scenario.

You've been hired as a consultant to design and implement a customer information
system for your client. The class you create has a 'customers' method that
returns a dictionary of all the customer objects.  Each customer object has an
'address' method that returns the a dictionary with information about the
customer's address.

The designers working for your client want to use information from your system
on the client's website --AND-- they want to understand the display code and so
they can maintian it themselves.


Using PSP, the display code for the website would look something like the
following, assuming your servlet subclasses the class you created for managing
customer information:

  <%= self.customer()[ID].address()['city'] %>   (42 chars)

Using Cheetah's NameMapper syntax it could be any of the following:

   $self.customers()[$ID].address()['city']       (39 chars)
   --OR--                                         
   $customers()[$ID].address()['city']           
   --OR--                                         
   $customers()[$ID].address().city              
   --OR--                                         
   $customers()[$ID].address.city                
   --OR--                                         
   $customers()[$ID].address.city
   --OR--
   $customers[$ID].address.city                   (27 chars)                   
   
   
Which of these would you prefer to explain to the designers, who have no
programming experience?  The last form is 15 characters shorter than the PSP
and, conceptually, is far more accessible. With PHP or ASP, the code would be
even messier than the PSP

This is a rather extreme example and, of course, you could also just implement
'$customer($ID).city' and obey the Law of Demeter (search Google for more on that).
But good object orientated design isn't the point here.

Details
================================================================================
The parenthesized letters below correspond to the aims in the second paragraph.

DICTIONARY ACCESS (a)
---------------------

NameMapper allows access to items in a dictionary using the same dotted notation
used to access object attributes in Python.  This aspect of NameMapper is known
as 'Unified Dotted Notation'.

For example, with Cheetah it is possible to write:
   $customers()['kerr'].address()  --OR--  $customers().kerr.address()
where the second form is in NameMapper syntax.

This only works with dictionary keys that are also valid python identifiers:
  regex = '[a-zA-Z_][a-zA-Z_0-9]*'


AUTOCALLING (b,d)
-----------------

NameMapper automatically detects functions and methods in Cheetah $vars and calls
them if the parentheses have been left off.  

For example if 'a' is an object, 'b' is a method
  $a.b
is equivalent to
  $a.b()

If b returns a dictionary, then following variations are possible
  $a.b.c  --OR--  $a.b().c  --OR--  $a.b()['c']
where 'c' is a key in the dictionary that a.b() returns.

Further notes:
* NameMapper autocalls the function or method without any arguments.  Thus
autocalling can only be used with functions or methods that either have no
arguments or have default values for all arguments.

* NameMapper only autocalls functions and methods.  Classes and callable objects
will not be autocalled.  

* Autocalling can be disabled using Cheetah's 'useAutocalling' setting.

LEAVING OUT 'self' (c,d)
------------------------

NameMapper makes it possible to access the attributes of a servlet in Cheetah
without needing to include 'self' in the variable names.  See the NAMESPACE
CASCADING section below for details.


UNDERSCORED ATTRIBUTES (d)
--------------------------

If a 'name' in cheetah doesn't correspond to a valid object attribute name in
Python, but there is an attribute in the form '_<name>' NameMapper will return
the underscored attribute.

Thus, it removes the need to change all placeholders like $clients.list to
$clients._list when the 'list' attribute of 'clients' is changed to underscored
attribute, and vice-versa.

NAMESPACE CASCADING (d)
--------------------

Implementation details
================================================================================

* NameMapper's search order is object attributes, then underscored attributes,
  and finally dictionary items.

* NameMapper.NotFound is raised if a value can't be found for a name.

Performance and the C version
================================================================================
Cheetah comes with both a C version and a Python Version of NameMapper.  The C
Version is up to 6 times faster.  It's slightly slower than standard Python
syntax, but you won't notice the speed difference in normal usage scenarios.

Cheetah uses the optimized C version (_namemapper.c) if it has
been compiled, or falls back automatically to the Python version if not.

Meta-Data
================================================================================
Authors: Tavis Rudd <tavis@calrudd.com>,
         Chuck Esterbrook <echuck@mindspring.com>
Version: $Revision: 1.18 $
Start Date: 2001/04/03
Last Revision Date: $Date: 2002/05/10 21:20:23 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>," +\
             "\nChuck Esterbrook <echuck@mindspring.com>"
__revision__ = "$Revision: 1.18 $"[11:-2]

##################################################
## DEPENDENCIES

import types
from types import StringType, InstanceType, ClassType, TypeType
import re
# it uses the string methods and list comprehensions added in recent versions of python

##################################################
## GLOBALS AND CONSTANTS

try:
    True,False
except NameError:
    True, False = (1==1),(1==0)

class NoDefault:
    pass

##################################################
## FUNCTIONS

try:
    from _namemapper import NotFound, valueForKey, valueForName, valueFromSearchList
    # it is possible, with Jython for example, that _namemapper.c hasn't been compiled
    C_VERSION = True
except:
    C_VERSION = False

    class NotFound(Exception):
        pass
    class NotFoundInNamespace(NotFound):
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
    
    def _valueForName(obj, nameChunks, executeCallables=False, passNamespace=False):
        ## go get a binding for the key ##
        firstKey = nameChunks[0]
        if passNamespace:
            try:
                binding = valueForKey(obj, firstKey)
            except NotFound:
                raise NotFoundInNamespace
        else:
            binding = valueForKey(obj, firstKey)
        if executeCallables and callable(binding) and \
           type(binding) not in (InstanceType, ClassType, TypeType):
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
                val = _valueForName(namespace, nameChunks,
                                    executeCallables=executeCallables, passNamespace=True)
                return val
            except NotFoundInNamespace:
                pass           
        raise NotFound(name)


##################################################
# these functions are not in the C version

def hasKey(obj, key):
    """Determine if 'obj' has 'key' """
    if hasattr(obj, key):
        return True
    elif hasattr(obj, '_' + key):
        return True
    elif hasattr(obj,'has_key') and obj.has_key(key):
        return True
    else:
        return False

def hasName(obj, name):
    """Determine if 'obj' has the 'name' """
    try:
        valueForName(obj, name)
        return True
    except NotFound:
        return False

##################################################
## CLASSES

class Mixin:
    """@@ document me"""
    def valueForName(self, name):
        return valueForName(self, name)

    def valueForKey(self, key):
        return valueForKey(self, key)

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

    print valueForKey(a.dic,'subDict')
    print valueForName(a, 'dic.item')
    print valueForName(vars(), 'b')
    print valueForName(__builtins__, 'dir')()
    print valueForName(vars(), 'a.classVar')
    print valueForName(vars(), 'B.underScoreVar')
    print valueForName(vars(), 'a.dic.func', executeCallables=True)
    print valueForName(vars(), 'a.method2.item1', executeCallables=True)

if __name__ == '__main__':
    example()



