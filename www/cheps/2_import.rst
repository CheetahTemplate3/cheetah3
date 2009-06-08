(#2) Conditionalized #import behavior
=====================================


:CHEP: 2
:Title: Conditionalized #import behavior
:Version: 1
:Author: R Tyler Ballance <tyler at slide.com>
:Status: Draft
:Type: Standards Track
:Content-Type: text/x-rst
:Created: 07-Jun-2009

----

Abstract
--------
This CHEP proposes an update to the way the #import and #from 
directives are handled such that locally scoped imports and 
module-level imports are handled appropriately.


Motivation
----------
Currently Cheetah (v2.2.1) provides two different, but mutually exclusive, 
means of importing Python modules with the #from/#import directives. The 
"traditional" handling for #from/#import is that the generated import 
statements shall all be relocated to the top of the generated module's 
source code, i.e. ::

    #import cjson

    Hello $cjson.encode([1, 2, 3])
    

Will result in generated module code along the lines of::

    import cjson

    class Foo(Template):
        def writeBody(self):
            write('Hello ')
            write(cjson.encode([1, 2, 3]))


Also currently in Cheetah is the ability to switch off this 
behavior and enable location specific #from/#import handling
in the generated code, with this block of Cheetah for example::

    #def aFunction(arg)
        #try
            #from hashlib import md5
        #except ImportError
            #from md5 import md5
        #end try
        #return $md5.new(arg).hexdigest()
    #end def

Will result in code generated with everything in
place such that the Python looks something like::

    class Foo(Template):
        def aFunction(self, arg):
            try:
                from hashlib import md5
            except ImportError:
                from md5 import md5
            return md5.new(arg).hexdigest()


These two approaches to handling the #from/#import directives
are both beneficial for different situations but currently they
are handled in mutually exclusive code paths and in mutually 
exclusive fashions. 

Specification
-------------

Rationale
---------

Backwards Compatibility
-----------------------

Reference Implementation
------------------------

Copyright
---------
This document has been placed in the public domain.
