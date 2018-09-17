.. role:: math(raw)
   :format: html latex

Language Overview
=================


Cheetah's basic syntax was inspired by the Java-based template
engines Velocity and WebMacro. It has two types of tags: {
$placeholders} and { #directives}. Both types are case-sensitive.

Placeholder tags begin with a dollar sign ({$varName}) and are
similar to data fields in a form letter or to the {%(key)s} fields
on the left side of Python's {%} operator. When the template is
filled, the placeholders are replaced with the values they refer
to.

Directive tags begin with a hash character (#) and are used for
comments, loops, conditional blocks, includes, and all other
advanced features. ({ Note:} you can customize the start and end
delimeters for placeholder and directive tags, but in this Guide
we'll assume you're using the default.)

Placeholders and directives can be escaped by putting a backslash
before them. ``\$var`` and ``\#if`` will be output as literal
text.

A placeholder or directive can span multiple physical lines,
following the same rules as Python source code: put a backslash
(``\``) at the end of all lines except the last line. However, if
there's an unclosed parenthesis, bracket or brace pending, you
don't need the backslash.

::

    #if $this_is_a_very_long_line and $has_lots_of_conditions \
        and $more_conditions:
    <H1>bla</H1>
    #end if

    #if $country in ('Argentina', 'Uruguay', 'Peru', 'Colombia',
        'Costa Rica', 'Venezuela', 'Mexico')
    <H1>Hola, senorita!</H1>
    #else
    <H1>Hey, baby!</H1>
    #end if

Language Constructs - Summary
-----------------------------



#. Comments and documentation strings


   #. {## single line}

   #. {#\* multi line \*#}


#. Generation, caching and filtering of output


   #. plain text

   #. look up a value: {$placeholder}

   #. evaluate an expression: {#echo} ...

   #. same but discard the output: {#silent} ...

   #. one-line if: {#if EXPR then EXPR else EXPR}

   #. gobble the EOL: {#slurp}

   #. parsed file includes: {#include} ...

   #. raw file includes: {#include raw} ...

   #. verbatim output of Cheetah code: {#raw} ... {#end raw}

   #. cached placeholders: {$\*var}, {$\*<interval>\*var}

   #. cached regions: {#cache} ... {#end cache}

   #. set the output filter: {#filter} ...

   #. control output indentation: {#indent} ... ({ not implemented
      yet})


#. Importing Python modules and objects: {#import} ..., {#from}
   ...

#. Inheritance


   #. set the base class to inherit from: {#extends}

   #. set the name of the main method to implement: {#implements}
      ...


#. Compile-time declaration


   #. define class attributes: {#attr} ...

   #. define class methods: {#def} ... {#end def}

   #. {#block} ... {#end block} provides a simplified interface to
      {#def} ... {#end def}


#. Run-time assignment


   #. local vars: {#set} ...

   #. global vars: {#set global} ...

   #. deleting local vars: {#del} ...


#. Flow control


   #. {#if} ... {#else} ... {#else if} (aka {#elif}) ... {#end if}

   #. {#unless} ... {#end unless}

   #. {#for} ... {#end for}

   #. {#repeat} ... {#end repeat}

   #. {#while} ... {#end while}

   #. {#break}

   #. {#continue}

   #. {#pass}

   #. {#stop}


#. error/exception handling


   #. {#assert}

   #. {#raise}

   #. {#try} ... {#except} ... {#else} ... {#end try}

   #. {#try} ... {#finally} ... {#end try}

   #. {#errorCatcher} ... set a handler for exceptions raised by
      $placeholder calls.


#. Instructions to the parser/compiler


   #. {#breakpoint}

   #. {#compiler-settings} ... {#end compiler-settings}


#. Escape to pure Python code


   #. evalute expression and print the output: {<%=} ... {%>}

   #. execute code and discard output: {<%} ... {%>}


#. Fine control over Cheetah-generated Python modules


   #. set the source code encoding of compiled template modules:
      {#encoding}

   #. set the sh-bang line of compiled template modules: {#shBang}



The use of all these constructs will be covered in the next several
chapters.

Placeholder Syntax Rules
------------------------



-  Placeholders follow the same syntax rules as Python variables
   except that they are preceded by {$} (the short form) or enclosed
   in {${}} (the long form). Examples:

   ::

       $var
       ${var}
       $var2.abc['def']('gh', $subplaceholder, 2)
       ${var2.abc['def']('gh', $subplaceholder, 2)}

   We recommend {$} in simple cases, and {${}} when followed directly
   by a letter or when Cheetah or a human template maintainer might
   get confused about where the placeholder ends. You may alternately
   use ``$()`` or ``$[]``, although this may confuse the (human)
   template maintainer:

   ::

       $(var)
       $[var]
       $(var2.abc['def']('gh', $subplaceholder, 2))
       $[var2.abc['def']('gh', $subplaceholder, 2)]

   { Note:} Advanced users can change the delimiters to anything they
   want via the {#compiler} directive.

   { Note 2:} The long form can be used only with top-level
   placeholders, not in expressions. See section
   language.placeholders.positions for an elaboration on this.

-  To reiterate Python's rules, placeholders consist of one or more
   identifiers separated by periods. Each identifier must start with a
   letter or an underscore, and the subsequent characters must be
   letters, digits or underscores. Any identifier may be followed by
   arguments enclosed in ``()`` and/or keys/subscripts in ``[]``.

-  Identifiers are case sensitive. {$var} does not equal {$Var} or
   {$vAr} or {$VAR}.

-  Arguments inside ``()`` or ``[]`` are just like in Python.
   Strings may be quoted using any Python quoting style. Each argument
   is an expression and may use any of Python's expression operators.
   Variables used in argument expressions are placeholders and should
   be prefixed with {$}. This also applies to the \*arg and \*\*kw
   forms. However, you do { not} need the {$} with the special Python
   constants {None}, {True} and {False}. Examples:

   ::

       $hex($myVar)
       $func($arg=1234)
       $func2($*args, $**kw)
       $func3(3.14159, $arg2, None, True)
       $myList[$mySubscript]

-  Trailing periods are ignored. Cheetah will recognize that the
   placeholder name in {$varName.} is {varName}, and the period will
   be left alone in the template output.

-  The syntax {${placeholderName, arg1="val1"}} passes arguments to
   the output filter (see {#filter}, section output.filter. The braces
   and comma are required in this case. It's conventional to omit the
   {$} before the keyword arguments (i.e. {arg1}) in this case.

-  Cheetah ignores all dollar signs ({$}) that are not followed by
   a letter or an underscore.


The following are valid $placeholders:

::

    $a $_ $var $_var $var1 $_1var $var2_ $dict.key $list[3]
    $object.method $object.method() $object.method
    $nest($nest($var))

These are not $placeholders but are treated as literal text:

::

    $@var $^var $15.50 $$

Where can you use placeholders?
-------------------------------


There are three places you can use placeholders: top-level
position, expression position and LVALUE position. Each has
slightly different syntax rules.

Top-level position means interspersed in text. This is the only
place you can use the placeholder long form: {${var}}.

{ Expression position} means inside a Cheetah expression, which is
the same as a Python expression. The placeholder names a searchList
or other variable to be read. Expression position occurs inside ()
and :math:`$[]$` arguments within placeholder tags (i.e., a
placeholder inside a placeholder), and in several directive tags.

{ LVALUE position} means naming a variable that will be written to.
LVALUE is a computer science term meaning
"the left side of an assignment statement". The first argument of
directives {#set}, {#for}, {#def}, {#block} and {#attr} is an
LVALUE.

This stupid example shows the three positions. Top-level position
is shown in {courier}, expression position is { italic}, and LVALUE
position is { bold}.

    #for { $count} in { $range}({ $ninetyNine}, 0, -1)
    #set { $after} = { $count} - 1
    {$count} bottles of beer on the wall. {$count} bottles of beer!
    Take one down, pass it around. {$after} bottles of beer on the
    wall.
    #end for
    {$hex}({ $myVar}, { $default}={ None})


The output of course is:

::

    99 bottles of beer on the wall.  99 bottles of beer!
        Take one down, pass it around.  98 bottles of beer on the wall.
    98 bottles of beer on the wall.  98 bottles of beer!
        Take one down, pass it around.  97 bottles of beer on the wall.
    ...

Are all those dollar signs really necessary?
--------------------------------------------


{$} is a "smart variable prefix". When Cheetah sees {$}, it
determines both the variable's position and whether it's a
searchList value or a non-searchList value, and generates the
appropriate Python code.

In top-level position, the {$} is { required}. Otherwise there's
nothing to distinguish the variable from ordinary text, and the
variable name is output verbatim.

In expression position, the {$} is { required} if the value comes
from the searchList or a "#set global" variable, { recommended} for
local/global/builtin variables, and { not necessary} for the
special constants {None}, {True} and {False}. This works because
Cheetah generates a function call for a searchList placeholder, but
a bare variable name for a local/global/builtin variable.

In LVALUE position, the {$} is { recommended}. Cheetah knows where
an LVALUE is expected, so it can handle your variable name whether
it has {$} or not.

EXCEPTION: Do { not} use the {$} prefix for intermediate variables
in a Python list comprehensions. This is a limitation of Cheetah's
parser; it can't tell which variables in a list comprehension are
the intermediate variables, so you have to help it. For example:

::

    #set $theRange = [x ** 2 for x in $range(10)]

{$theRange} is a regular {#set} variable. {$range} is a Python
built-in function. But {x} is a scratch variable internal to the
list comprehension: if you type {$x}, Cheetah will miscompile it.

NameMapper Syntax
-----------------


One of our core aims for Cheetah was to make it easy for
non-programmers to use. Therefore, Cheetah uses a simplified syntax
for mapping placeholders in Cheetah to values in Python. It's known
as the { NameMapper syntax} and allows for non-programmers to use
Cheetah without knowing (a) the difference between an instance and
a dictionary, (b) what functions and methods are, and (c) what
'self' is. A side benefit is that you can change the underlying
data structure (e.g., instance to dictionary or vice-versa) without
having to modify the templates.

NameMapper syntax is used for all variables in Cheetah placeholders
and directives. If desired, it can be turned off via the {Template}
class' {'useNameMapper'} compiler setting. But it's doubtful you'd
ever want to turn it off.

Example
~~~~~~~


Consider this scenario:

You are building a customer information system. The designers with
you want to use information from your system on the client's
website -AND- they want to understand the display code and so they
can maintian it themselves.

You write a UI class with a 'customers' method that returns a
dictionary of all the customer objects. Each customer object has an
'address' method that returns the a dictionary with information
about the customer's address. The designers want to be able to
access that information.

Using PSP, the display code for the website would look something
like the following, assuming your servlet subclasses the class you
created for managing customer information:

::

      <%= self.customer()[ID].address()['city'] %>   (42 chars)

With Cheetah's NameMapper syntax, you can use any of the
following:

::

       $self.customers()[$ID].address()['city']       (39 chars)
       --OR--
       $customers()[$ID].address()['city']
       --OR--
       $customers()[$ID].address().city
       --OR--
       $customers()[$ID].address.city
       --OR--
       $customers[$ID].address.city                   (27 chars)

Which of these would you prefer to explain to the designers, who
have no programming experience? The last form is 15 characters
shorter than the PSP version and - conceptually - far more
accessible. With PHP or ASP, the code would be even messier than
with PSP.

This is a rather extreme example and, of course, you could also
just implement {$getCustomer($ID).city} and obey the Law of Demeter
(search Google for more on that). But good object orientated design
isn't the point of this example.

Dictionary Access
~~~~~~~~~~~~~~~~~


NameMapper syntax allows access to dictionary items with the same
dotted notation used to access object attributes in Python. This
aspect of NameMapper syntax is known as 'Unified Dotted Notation'.
For example, with Cheetah it is possible to write:

::

       $customers()['kerr'].address()  --OR--  $customers().kerr.address()

where the second form is in NameMapper syntax.

This works only with dictionary keys that also happen to be valid
Python identifiers.

Autocalling
~~~~~~~~~~~


Cheetah automatically detects functions and methods in Cheetah
$variables and calls them if the parentheses have been left off.
Our previous example can be further simplified to:

::

      $customers.kerr.address

As another example, if 'a' is an object, 'b' is a method

::

      $a.b

is equivalent to

::

      $a.b()

If b returns a dictionary, then following variations are possible

::

      $a.b.c  --OR--  $a.b().c  --OR--  $a.b()['c']

where 'c' is a key in the dictionary that a.b() returns.

Further notes:


-  When Cheetah autocalls a function/method, it calls it without
   any arguments. Thus, the function/method must have been declared
   without arguments (except {self} for methods) or to provide default
   values for all arguments. If the function requires arguments, you
   must use the {()}.

-  Cheetah autocalls only functions and methods. Classes and other
   callable objects are not autocalled. The reason is that the primary
   purpose of a function/method is to call it, whereas the primary
   purpose of an instance is to look up its attributes or call its
   methods, not to call the instance itself. And calling a class may
   allocate large sums of memory uselessly or have other side effects,
   depending on the class. For instance, consider {$myInstance.fname}.
   Do we want to look up {fname} in the namespace of {myInstance} or
   in the namespace of whatever {myinstance} returns? It could go
   either way, so Cheetah follows the principle of least surprise. If
   you { do} want to call the instance, put the {()} on, or rename the
   {.\_\_call\_\_()} method to {.\_\_str\_\_}.

-  Autocalling can be disabled via Cheetah's 'useAutocalling'
   compiler setting. You can also disable it for one placeholder by
   using the syntax {$getVar('varName', 'default value', False)}.
   ({.getVar()} works only with searchList values.)


Namespace cascading and the searchList
--------------------------------------


When Cheetah maps a variable name in a template to a Python value,
it searches several namespaces in order:


#. { Local variables:} created by {#set}, {#for}, or predefined by
   Cheetah.

#. The { searchList}, consisting of:


   #. {#set global} variables.

   #. The { searchList} containers you passed to the {Template}
      constructor, if any.

   #. The { Template instance} ("self"). This contains any attributes
      you assigned, {#def} methods and {#block methods},
      attributes/methods inherited via {#extends}, and other
      attributes/methods built into {Template} or inherited by it
      (there's a list of all these methods in section tips.allMethods).


#. { Python globals:} created by {#import}, {#from ... import}, or
   otherwise predefined by Cheetah.

#. { Python builtins:} {None}, {max}, etc.


The first matching name found is used.

Remember, these namespaces apply only to the { first} identifier
after the {$}. In a placeholder like {$a.b}, only 'a' is looked up
in the searchList and other namespaces. 'b' is looked up only
inside 'a'.

A searchList container can be any Python object with attributes or
keys: dictionaries, instances, classes or modules. If an instance
contains both attributes and keys, its attributes are searched
first, then its keys.

Because the {Template} instance is part of the searchList, you can
access its attributes/methods without 'self': {$myAttr}. However,
use the 'self' if you want to make sure you're getting the
{Template} attribute and not a same-name variable defined in a
higher namespace: {$self.myAttr}. This works because "self" itself
is a local variable.

The final resulting value, after all lookups and function calls
(but before the filter is applied) is called the { placeholder
value}, no matter which namespace it was found in.

{ { Note carefully:}} if you put an object 'myObject' in the
searchList, you { cannot} look up {$myObject}! You can look up only
the attributes/keys { inside} 'myObject'.

Earlier versions of Cheetah did not allow you to override Python
builtin names, but this was fixed in Cheetah 0.9.15.

If your template will be used as a Webware servlet, do not override
methods 'name' and 'log' in the {Template} instance or it will
interfere with Webware's logging. However, it { is} OK to use those
variables in a higher namespace, since Webware doesn't know about
Cheetah namespaces.

Missing Values
--------------


If NameMapper can not find a Python value for a Cheetah variable
name, it will raise the NameMapper.NotFound exception. You can use
the {#errorCatcher} directive (section errorHandling.errorCatcher)
or { errorCatcher} Template constructor argument (section
howWorks.constructing) to specify an alternate behaviour. BUT BE
AWARE THAT errorCatcher IS ONLY INTENDED FOR DEBUGGING!

To provide a default value for a placeholder, write it like this:
{$getVar('varName', 'default value')}. If you don't specify a
default and the variable is missing, {NameMapper.NotFound} will be
raised.

Directive Syntax Rules
----------------------


Directive tags begin with a hash character (#) and are used for
comments, loops, conditional blocks, includes, and all other
advanced features. Cheetah uses a Python-like syntax inside
directive tags and understands any valid Python expression. {
However, unlike Python, Cheetah does not use colons (:) and
indentation to mark off multi-line directives.} That doesn't work
in an environment where whitespace is significant as part of the
text. Instead, multi-line directives like {#for} have corresponding
closing tags ({#end for}). Most directives are direct mirrors of
Python statements.

Many directives have arguments after the opening tag, which must be
in the specified syntax for the tag. All end tags have the
following syntax:

::

    #end TAG_NAME [EXPR]

The expression is ignored, so it's essentially a comment.

Directive closures and whitespace handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

(language.directives.closures) Directive tags can be closed
explicitly with {#}, or implicitly with the end of the line if
you're feeling lazy.

::

    #block testBlock #
    Text in the body of the
    block directive
    #end block testBlock #

is identical to:

::

    #block testBlock
    Text in the body of the
    block directive
    #end block testBlock

When a directive tag is closed explicitly, it can be followed with
other text on the same line:

::

    bah, bah, #if $sheep.color == 'black'# black#end if # sheep.

When a directive tag is closed implicitly with the end of the line,
all trailing whitespace is gobbled, including the newline
character:

::

    """
    foo #set $x = 2
    bar
    """
    outputs
    """
    foo bar
    """

    while
    """
    foo #set $x = 2 #
    bar
    """
    outputs
    """
    foo
    bar
    """

When a directive tag is closed implicitly AND there is no other
text on the line, the ENTIRE line is gobbled up including any
preceeding whitespace:

::

    """
    foo
       #set $x = 2
    bar
    """
    outputs
    """
    foo
    bar
    """

    while
    """
    foo
     - #set $x = 2
    bar
    """
    outputs
    """
    foo
     - bar
    """

The {#slurp} directive (section output.slurp) also gobbles up
whitespace.

Spaces outside directives are output { exactly} as written. In the
black sheep example, there's a space before "black" and another
before "sheep". So although it's legal to put multiple directives
on one line, it can be hard to read.

::

    #if $a# #echo $a + 1# #end if
          - There's a space between each directive,
            or two extra spaces total.
    #if $a##echo $a + 1##end if
          - No spaces, but you have to look closely
            to verify none of the ``##'' are comment markers.
    #if $a##echo $a + 1##end if     ### A comment.
          - In ``###'', the first ``#'' ends the directive,
            the other two begin the comment.  (This also shows
        how you can add extra whitespace in the directive
        tag without affecting the output.)
    #if $a##echo $a + 1##end if     # ## A comment.
          - More readable, but now there's a space before the
            comment.


