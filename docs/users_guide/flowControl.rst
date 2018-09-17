Flow Control
============


#for ... #end for
-----------------


Syntax:

::

    #for $var in EXPR
    #end for

The {#for} directive iterates through a sequence. The syntax is the
same as Python, but remember the {$} before variables.

Here's a simple client listing:

::

    <TABLE>
    #for $client in $service.clients
    <TR>
    <TD>$client.surname, $client.firstname</TD>
    <TD><A HREF="mailto:$client.email" >$client.email</A></TD>
    </TR>
    #end for
    </TABLE>

Here's how to loop through the keys and values of a dictionary:

::

    <PRE>
    #for $key, $value in $dict.items()
    $key: $value
    #end for
    </PRE>

Here's how to create list of numbers separated by hyphens. This
"#end for" tag shares the last line to avoid introducing a newline
character after each hyphen.

::

    #for $i in range(15)
    $i - #end for

If the location of the {#end for} offends your sense of
indentational propriety, you can do this instead:

::

    #for $i in $range(15)
    $i - #slurp
    #end for

The previous two examples will put an extra hyphen after last
number. Here's how to get around that problem, using the {#set}
directive, which will be dealt with in more detail below.

::

    #set $sep = ''
    #for $name in $names
    $sep$name
    #set $sep = ', '
    #end for

Although to just put a separator between strings, you don't need a
for loop:

::

    #echo ', '.join($names)

#repeat ... #end repeat
-----------------------


Syntax:

::

    #repeat EXPR
    #end repeat

Do something a certain number of times. The argument may be any
numeric expression. If it's zero or negative, the loop will execute
zero times.

::

    #repeat $times + 3
    She loves me, she loves me not.
    #repeat
    She loves me.

Inside the loop, there's no way to tell which iteration you're on.
If you need a counter variable, use {#for} instead with Python's
{range} function. Since Python's ranges are base 0 by default,
there are two ways to start counting at 1. Say we want to count
from 1 to 5, and that {$count} is 5.

::

    #for $i in $range($count)
    #set $step = $i + 1
    $step.  Counting from 1 to $count.
    #end for


    #for $i in $range(1, $count + 1)
    $i.  Counting from 1 to $count.
    #end for

A previous implementation used a local variable {$i} as the repeat
counter. However, this prevented instances of {#repeat} from being
nested. The current implementation does not have this problem as it
uses a new local variable for every instance of {#repeat}.

#while ... #end while
---------------------


Syntax:

::

    #while EXPR
    #end while

{#while} is the same as Python's {while} statement. It may be
followed by any boolean expression:

::

    #while $someCondition('arg1', $arg2)
    The condition is true.
    #end while

Be careful not to create an infinite loop. {#while 1} will loop
until the computer runs out of memory.

#if ... #else if ... #else ... #end if
--------------------------------------


Syntax:

::

    #if EXPR
    #else if EXPR
    #elif EXPR
    #else
    #end if

The {#if} directive and its kin are used to display a portion of
text conditionally. {#if} and {#else if} should be followed by a
true/false expression, while {#else} should not. Any valid Python
expression is allowed. As in Python, the expression is true unless
it evaluates to 0, '', None, an empty list, or an empty dictionary.
In deference to Python, {#elif} is accepted as a synonym for {#else
if}.

Here are some examples:

::

    #if $size >= 1500
    It's big
    #else if $size < 1500 and $size > 0
    It's small
    #else
    It's not there
    #end if

::

    #if $testItem($item)
    The item $item.name is OK.
    #end if

Here's an example that combines an {#if} tag with a {#for} tag.

::

    #if $people
    <table>
    <tr>
    <th>Name</th>
    <th>Address</th>
    <th>Phone</th>
    </tr>
    #for $p in $people
    <tr>
    <td>$p.name</td>
    <td>$p.address</td>
    <td>$p.phone</td>
    </tr>
    #end for
    </table>
    #else
    <p> Sorry, the search did not find any people. </p>
    #end if

See section output.oneLineIf for the one-line {#if} directive,
which is equivalent to Perl's and C's {?:} operator.

#unless ... #end unless
-----------------------


Syntax:

::

    #unless EXPR
    #end unless

{#unless} is the opposite of {#if}: the text is executed if the
condition is { false}. Sometimes this is more convenient. {#unless
EXPR} is equivalent to {#if not (EXPR)}.

::

    #unless $alive
    This parrot is no more!  He has ceased to be!
    'E's expired and gone to meet 'is maker! ...
    THIS IS AN EX-PARROT!!
    #end unless

You cannot use {#else if} or {#else} inside an {#unless} construct.
If you need those, use {#if} instead.

#break and #continue
--------------------


Syntax:

::

    #break
    #continue

These directives are used as in Python. {#break} will exit a {#for}
loop prematurely, while {#continue} will immediately jump to the
next iteration in the {#for} loop.

In this example the output list will not contain "10 -".

::

    #for $i in range(15)
    #if $i == 10
      #continue
    #end if
    $i - #slurp
    #end for

In this example the loop will exit if it finds a name that equals
'Joe':

::

    #for $name in $names
    #if $name == 'Joe'
      #break
    #end if
    $name - #slurp
    #end for

#pass
-----


Syntax:

::

    #pass

The {#pass} directive is identical to Python {pass} statement: it
does nothing. It can be used when a statement is required
syntactically but the program requires no action.

The following example does nothing if only $A is true

::

    #if $A and $B
       do something
    #elif $A
      #pass
    #elif $B
      do something
    #else
      do something
    #end if

#stop
-----


Syntax:

::

    #stop

The {#stop} directive is used to stop processing of a template at a
certain point. The output will show { only} what has been processed
up to that point.

When {#stop} is called inside an {#include} it skips the rest of
the included code and continues on from after the {#include}
directive. stop the processing of the included code. Likewise, when
{#stop} is called inside a {#def} or {#block}, it stops only the
{#def} or {#block}.

::

    A cat
    #if 1
      sat on a mat
      #stop
      watching a rat
    #end if
    in a flat.

will print

::

    A cat
      sat on a mat

And

::

    A cat
    #block action
      sat on a mat
      #stop
      watching a rat
    #end block
    in a flat.

will print

::

    A cat
      sat on a mat
    in a flat.

#return
-------


Syntax:

::

    #return

This is used as in Python. {#return} will exit the current method
with a default return value of {None} or the value specified. It
may be used only inside a {#def} or a {#block}.

Note that {#return} is different from the {#stop} directive, which
returns the sum of all text output from the method in which it is
called. The following examples illustrate this point:

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

will produce

::

    1
    2
    3

while

::

    1
    $test
    3
    #def test
    1.5
    #if 1
    #stop
    #else
    99999
    #end if
    #end def

will produce

::

    1
    1.5
    3


