Directives: Import, Inheritance, Declaration and Assignment
===========================================================


#import and #from
-----------------


The template:

::

    #import math

This construct does not produce any output.

The generated module, at the bottom of the import section:

::

    import math

#extends
--------


The template:

::

    #extends SomeClass

The generated import (skipped if {SomeClass} has already been
imported):

::

    from SomeClass import SomeClass

The generated class:

::

    class x(SomeClass):

#implements
-----------


The template:

::

    #implements doOutput

In the generated class, the main method is {.doOutput} instead of
{.respond}, and the attribute naming this method is:

::

    _mainCheetahMethod_for_x2= 'doOutput'

#set and #set global
--------------------


The template:

::

    #set $namesList = ['Moe','Larry','Curly']
    $namesList
    #set global $toes = ['eeny', 'meeny', 'miney', 'moe']
    $toes

The output:

::

    ['Moe', 'Larry', 'Curly']
    ['eeny', 'meeny', 'miney', 'moe']

The generated code:

::

    1  namesList = ['Moe','Larry','Curly']
    2  write(filter(namesList)) # generated from '$namesList' at line 2, col 1.
    3  write('\n')
    4  globalSetVars["toes"] = ['eeny', 'meeny', 'miney', 'moe']
    5  write(filter(VFS(SL,"toes",1))) # generated from '$toes' at line 4, col 1.
    6  write('\n')

{globalSetVars} is a local variable referencing {.\_globalSetVars}.
Writes go into it directly, but reads take advantage of the fact
that {.\_globalSetVars} is on the searchList. (In fact, it's the
very first namespace.)

#del
----


The template:

::

    #set $a = 1
    #del $a
    #set $a = 2
    #set $arr = [0, 1, 2]
    #del $a, $arr[1]

In the generated class:

::

    1  a = 1
    2  del a
    3  a = 2
    4  arr = [0, 1, 2]
    5  del a, arr[1]

#attr
-----


The template:

::

    #attr $namesList = ['Moe', 'Larry', 'Curly']

In the generated class:

::

    ## GENERATED ATTRIBUTES

    namesList = ['Moe', 'Larry', 'Curly']

#def
----


The template:

::

    #def printArg($arg)
    The argument is $arg.
    #end def
    My method returned $printArg(5).

The output:

::

    My method returned The argument is 5.
    .

Hmm, not exactly what we expected. The method returns a trailing
newline because we didn't end the last line with {#slurp}. So the
second period (outside the method) appears on a separate line.

The {#def} generates a method {.printArg} whose structure is
similar to the main method:

::

    def printArg(self,
            arg,
            trans=None,
            dummyTrans=False,
            VFS=valueFromSearchList,
            VFN=valueForName,
            getmtime=getmtime,
            currentTime=time.time):


        """
        Generated from #def printArg($arg) at line 1, col 1.
        """

        if not trans:
            trans = DummyTransaction()
            dummyTrans = True
        write = trans.response().write
        SL = self._searchList
        filter = self._currentFilter
        globalSetVars = self._globalSetVars

        ########################################
        ## START - generated method body

        write('The argument is ')
        write(filter(arg)) # generated from '$arg' at line 2, col 17.
        write('.\n')

        ########################################
        ## END - generated method body

        if dummyTrans:
            return trans.response().getvalue()
        else:
            return ""

When {.printArg} is called from a placeholder, only the arguments
the user supplied are passed. The other arguments retain their
default values.

#block
------


The template:

::

    #block content
    This page is under construction.
    #end block

The output:

::

    This page is under construction.

This construct generates a method {.content} in the same structure
as {.printArg} above, containing the write code:

::

    write('This page is under construction.\n')

In the main method, the write code is:

::

    self.content(trans=trans) # generated from ('content', '#block content')
        # at line 1, col 1.

So a block placeholder implicitly passes the current transaction to
the method.


