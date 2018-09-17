Directives: Flow Control
========================


#for
----


The template:

::

    #for $i in $range(10)
    $i #slurp
    #end for

The output:

::

    0 1 2 3 4 5 6 7 8 9

The generated code:

::

    for i in range(10):
        write(filter(i)) # generated from '$i' at line 2, col 1.
        write(' ')

#repeat
-------


The template:

::

    #repeat 3
    My bonnie lies over the ocean
    #end repeat
    O, bring back my bonnie to me!

The output:

::

    My bonnie lies over the ocean
    My bonnie lies over the ocean
    My bonnie lies over the ocean
    O, bring back my bonnie to me!


The generated code:

::

    for __i0 in range(3):
        write('My bonnie lies over the ocean\n')
    write('O, bring back my bonnie to me!\n')

Note that a new local variable of the form {\_\_i$num} will be used
for each instance of {repeat} in order to permit nesting.

#while
------


The template:

::

    #set $alive = True
    #while $alive
    I am alive!
    #set $alive = False
    #end while

The output:

::

    I am alive!

The generated code:

::

    alive = True
    while alive:
        write('I am alive!\n')
        alive = False

#if
---

()

The template:

::

    #set $size = 500
    #if $size >= 1500
    It's big
    #else if $size < 1500 and $size > 0
    It's small
    #else
    It's not there
    #end if

The output:

::

    It's small

The generated code:

::

    size = 500
    if size >= 1500:
        write("It's big\n")
    elif size < 1500 and size > 0:
        write("It's small\n")
    else:
        write("It's not there\n")

#unless
-------


The template:

::

    #set $count = 9
    #unless $count + 5 > 15
    Count is in range.
    #end unless

The output:

::

    Count is in range.

The generated code:

::

            count = 9
            if not (count + 5 > 15):
                write('Count is in range.\n')

{ Note:} There is a bug in Cheetah 0.9.13. It's forgetting the
parentheses in the {if} expression, which could lead to it
calculating something different than it should.

#break and #continue
--------------------


The template:

::

    #for $i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 'James', 'Joe', 'Snow']
    #if $i == 10
      #continue
    #end if
    #if $i == 'Joe'
      #break
    #end if
    $i - #slurp
    #end for

The output:

::

    1 - 2 - 3 - 4 - 5 - 6 - 7 - 8 - 9 - 11 - 12 - James -

The generated code:

::

    for i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 'James', 'Joe', 'Snow']:
        if i == 10:
            write('')
            continue
        if i == 'Joe':
            write('')
            break
        write(filter(i)) # generated from '$i' at line 8, col 1.
        write(' - ')

#pass
-----


The template:

::

    Let's check the number.
    #set $size = 500
    #if $size >= 1500
    It's big
    #elif $size > 0
    #pass
    #else
    Invalid entry
    #end if
    Done checking the number.

The output:

::

    Let's check the number.
    Done checking the number.

The generated code:

::

    write("Let's check the number.\n")
    size = 500
    if size >= 1500:
        write("It's big\n")
    elif size > 0:
        pass
    else:
        write('Invalid entry\n')
    write('Done checking the number.\n')

#stop
-----


The template:

::

    A cat
    #if 1
      sat on a mat
      #stop
      watching a rat
    #end if
    in a flat.

The output:

::

    A cat
      sat on a mat

The generated code:

::

    write('A cat\n')
    if 1:
        write('  sat on a mat\n')
        if dummyTrans:
            return trans.response().getvalue()
        else:
            return ""
        write('  watching a rat\n')
    write('in a flat.\n')

#return
-------


The template:

::

    1
    $test[1]
    3
    #def test
    1.5
    #if 1
    #return '123'
    #else
    99999
    #end if
    #end def

The output:

::

    1
    2
    3

The generated code:

::

        def test(self,
                trans=None,
                dummyTrans=False,
                VFS=valueFromSearchList,
                VFN=valueForName,
                getmtime=getmtime,
                currentTime=time.time):


            """
            Generated from #def test at line 5, col 1.
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

            write('1.5\n')
            if 1:
                return '123'
            else:
                write('99999\n')

            ########################################
            ## END - generated method body

            if dummyTrans:
                return trans.response().getvalue()
            else:
                return ""

::

        def respond(self,
                trans=None,
                dummyTrans=False,
                VFS=valueFromSearchList,
                VFN=valueForName,
                getmtime=getmtime,
                currentTime=time.time):


            """
            This is the main method generated by Cheetah
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

            write('\n1\n')
            write(filter(VFS(SL,"test",1)[1])) # generated from '$test[1]' at line 3, col 1.
            write('\n3\n')

            ########################################
            ## END - generated method body

            if dummyTrans:
                return trans.response().getvalue()
            else:
                return ""


