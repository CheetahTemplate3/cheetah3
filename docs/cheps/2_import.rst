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
"traditional" handling for #from/#import (hereafter referred to as "module imports")
is that the generated import statements shall all be relocated to
the top of the generated module's source code, i.e. ::

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
(hereafter referred to as "function imports") in the generated
code, with this block of Cheetah for example::

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
The change in #from/#import behavior and how these directives
are handled is all based on context of their use, making the
#from/#import handling "intelligent". For module imports, the
"traditional" handling of the #from/#import directives will
still apply. Whereas function imports will result in inline
generated import code.

The basic premise of the change proposed by this document is
that all #from/#import directives contained within a #def/#end def
closure will result in import statements contained within that
function block whereas everywhere else the statements will be relocated
to the top of the generated module code (i.e. the module import)


Rationale
---------
The concept of the "function import" was introduced in Cheetah v2.1.0
and quickly retrofitted to "live" behind a compiler setting due to the
regressions with older templates or templates that were designed to utilize
module imports (through heavy #block/#end block use, etc). Through discussion
with Tavis Rudd, this middle ground between the two styles of importing was
concluded to be the most reasonable solution to providing "pythonic" import
functionality (i.e. "function import" also known as "inline imports") while
still providing the ability to have #from/#import directives declared at the
module scope within the template (within the Cheetah templates, markup and most
directives declared within the module scope are placed inside the default method).


Backwards Compatibility
-----------------------
Changes proposed in this document should be *mostly* backwards
compatible with current versions of Cheetah, Any unforeseen issues
could arise from the use of #from/#import inside of a function
expecting those symbols to be available outside of the function
that they're declared in.


Reference Implementation
------------------------
*still in development*

Copyright
---------
This document has been placed in the public domain.
