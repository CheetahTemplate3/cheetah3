Import, Inheritance, Declaration and Assignment
===============================================


#import and #from directives
----------------------------


Syntax:

::

    #import MODULE_OR_OBJECT [as NAME] [, ...]
    #from MODULE import MODULE_OR_OBJECT [as NAME] [, ...]

The {#import} and {#from} directives are used to make external
Python modules or objects available to placeholders. The syntax is
identical to the import syntax in Python. Imported modules are
visible globally to all methods in the generated Python class.

::

    #import math
    #import math as mathModule
    #from math import sin, cos
    #from math import sin as _sin
    #import random, re
    #from mx import DateTime         # ## Part of Egenix's mx package.

After the above imports, {$math}, {$mathModule}, {$sin}, {$cos} and
{$\_sin}, {$random}, {$re} and {$DateTime} may be used in
{$placeholders} and expressions.

#extends
--------


Syntax:

::

    #extends CLASS

All templates are subclasses of {Cheetah.Template.Template}.
However, it's possible for a template to subclass another template
or a pure Python class. This is where {#extends} steps in: it
specifies the parent class. It's equivalent to PSP's
{"@page extends="} directive.

Cheetah imports the class mentioned in an {#extends} directive
automatically if you haven't imported it yet. The implicit
importing works like this:

::

    #extends Superclass
    ## Implicitly does '#from Superclass import Superclass'.

    #extends Cheetah.Templates.SkeletonPage
    ## Implicitly does '#from Cheetah.Templates.SkeletonPage import SkeletonPage'.

If your superclass is in an unusual location or in a module named
differently than the class, you must import it explicitly. There is
no support for extending from a class that is not imported; e.g.,
from a template dynamically created from a string. Since the most
practical way to get a parent template into a module is to
precompile it, all parent templates essentially have to be
precompiled.

There can be only one {#extends} directive in a template and it may
list only one class. In other words, templates don't do multiple
inheritance. This is intentional: it's too hard to initialize
multiple base classes correctly from inside a template. However,
you can do multiple inheritance in your pure Python classes.

If your pure Python class overrides any of the standard {Template}
methods such as {.\_\_init\_\_} or {.awake}, be sure to call the
superclass method in your method or things will break. Examples of
calling the superclass method are in section
tips.callingSuperclassMethods. A list of all superclass methods is
in section tips.allMethods.

In all cases, the root superclass must be {Template}. If your
bottommost class is a template, simply omit the {#extends} in it
and it will automatically inherit from {Template}. { If your
bottommost class is a pure Python class, it must inherit from
{Template} explicitly: }

::

    from Cheetah.Template import Template
    class MyPurePythonClass(Template):

If you're not keen about having your Python classes inherit from
{Template}, create a tiny glue class that inherits both from your
class and from {Template}.

Before giving any examples we'll stress that Cheetah does { not}
dictate how you should structure your inheritance tree. As long as
you follow the rules above, many structures are possible.

Here's an example for a large web site that has not only a general
site template, but also a template for this section of the site,
and then a specific template-servlet for each URL. (This is the
"inheritance approach" discussed in the Webware chapter.) Each
template inherits from a pure Python class that contains
methods/attributes used by the template. We'll begin with the
bottommost superclass and end with the specific template-servlet:

::

    1.  SiteLogic.py (pure Python class containing methods for the site)
            from Cheetah.Template import Template
            class SiteLogic(Template):

    2.  Site.tmpl/py  (template containing the general site framework;
                       this is the template that controls the output,
                       the one that contains "<HTML><HEAD>...", the one
                       that contains text outside any #def/#block.)
            #from SiteLogic import SiteLogic
            #extends SiteLogic
            #implements respond

    3.  SectionLogic.py  (pure Python class with helper code for the section)
            from Site import Site
            class SectionLogic(Site)

    4.  Section.tmpl/py  (template with '#def' overrides etc. for the section)
            #from SectionLogic import SectionLogic
            #extends SectionLogic

    5.  page1Logic.py  (pure Python class with helper code for the template-servlet)
            from Section import Section
            class indexLogic(Section):

    6.  page1.tmpl/py  (template-servlet for a certain page on the site)
            #from page1Logic import page1Logic
            #extends page1Logic

A pure Python classes might also contain methods/attributes that
aren't used by their immediate child template, but are available
for any descendant template to use if it wishes. For instance, the
site template might have attributes for the name and e-mail address
of the site administrator, ready to use as $placeholders in any
template that wants it.

{ Whenever you use {#extends}, you often need {#implements} too,}
as in step 2 above. Read the next section to understand what
{#implements} is and when to use it.

#implements
-----------


Syntax:

::

    #implements METHOD

You can call any {#def} or {#block} method directly and get its
outpt. The top-level content - all the text/placeholders/directives
outside any {#def}/{#block} - gets concatenated and wrapped in a
"main method", by default {.respond()}. So if you call
{.respond()}, you get the "whole template output". When Webware
calls {.respond()}, that's what it's doing. And when you do 'print
t' or 'str(t)' on a template instance, you're taking advantage of
the fact that Cheetah makes {.\_\_str\_\_()} an alias for the main
method.

That's all fine and dandy, but what if your application prefers to
call another method name rather than {.respond()}? What if it wants
to call, say, {.send\_output()} instead? That's where {#implements}
steps in. It lets you choose the name for the main method. Just put
this in your template definition:

::

    #implements send_output

When one template extends another, every template in the
inheritance chain has its own main method. To fill the template,
you invoke exactly one of these methods and the others are ignored.
The method you call may be in any of the templates in the
inheritance chain: the base template, the leaf template, or any in
between, depending on how you structure your application. So you
have two problems: (1) calling the right method name, and (2)
preventing an undesired same-name subclass method from overriding
the one you want to call.

Cheetah assumes the method you will call is {.respond()} because
that's what Webware calls. It further assumes the desired main
method is the one in the lowest-level base template, because that
works well with {#block} as described in the Inheritance Approach
for building Webware servlets (section webware.inheritance), which
was originally the principal use for Cheetah. So when you use
{#extends}, Cheetah changes that template's main method to
{.writeBody()} to get it out of the way and prevent it from
overriding the base template's {.respond()}.

Unfortunately this assumption breaks down if the template is used
in other ways. For instance, you may want to use the main method in
the highest-level leaf template, and treat the base template(s) as
merely a library of methods/attributes. In that case, the leaf
template needs {#implements respond} to change its main method name
back to {.respond()} (or whatever your application desires to
call). Likewise, if your main method is in one of the intermediate
templates in an inheritance chain, that template needs {#implements
respond}.

The other way the assumption breaks down is if the main method {
is} in the base template but that template extends a pure Python
class. Cheetah sees the {#extends} and dutifully but incorrectly
renames the method to {.writeBody()}, so you have to use
{#implements respond} to change it back. Otherwise the dummy
{.respond()} in {Cheetah.Template} is found, which outputs...
nothing. { So if you're using {#extends} and get no output, the {
first} thing you should think is,
"Do I need to add {#implements respond} somewhere?" }

#set
----


Syntax:

::

    #set [global] $var = EXPR

{#set} is used to create and update local variables at run time.
The expression may be any Python expression. Remember to preface
variable names with $ unless they're part of an intermediate result
in a list comprehension.

Here are some examples:

::

    #set $size = $length * 1096
    #set $buffer = $size + 1096
    #set $area = $length * $width
    #set $namesList = ['Moe','Larry','Curly']
    #set $prettyCountry = $country.replace(' ', '&nbsp;')

{#set} variables are useful to assign a short name to a
{$deeply.nested.value}, to a calculation, or to a printable version
of a value. The last example above converts any spaces in the
'country' value into HTML non-breakable-space entities, to ensure
the entire value appears on one line in the browser.

{#set} variables are also useful in {#if} expressions, but remember
that complex logical routines should be coded in Python, not in
Cheetah!

::

    #if $size > 1500
      #set $adj = 'large'
    #else
      #set $adj = 'small'
    #end if

Or Python's one-line equivalent, "A and B or C". Remember that in
this case, B must be a true value (not None, '', 0, [] or {}).

::

    #set $adj = $size > 1500 and 'large' or 'small'

(Note: Cheetah's one-line {#if} will not work for this, since it
produces output rather than setting a variable.

You can also use the augmented assignment operators:

::

    ## Increment $a by 5.
    #set $a += 5

By default, {#set} variables are not visible in method calls or
include files unless you use the {global} attribute: {#set global
$var = EXPRESSION}. Global variables are visible in all methods,
nested templates and included files. Use this feature with care to
prevent surprises.

#del
----


Syntax:

::

    #del $var

{#del} is the opposite of {#set}. It deletes a { local} variable.
Its usage is just like Python's {del} statement:

::

    #del $myVar
    #del $myVar, $myArray[5]

Only local variables can be deleted. There is no directive to
delete a {#set global} variable, a searchList variable, or any
other type of variable.

#attr
-----


Syntax:

::

    #attr $var = EXPR

The {#attr} directive creates class attributes in the generated
Python class. It should be used to assign simple Python literals
such as numbers or strings. In particular, the expression must {
not} depend on searchList values or {#set} variables since those
are not known at compile time.

::

    #attr $title = "Rob Roy"
    #attr $author = "Sir Walter Scott"
    #attr $version = 123.4

This template or any child template can output the value thus:

::

    $title, by $author, version $version

If you have a library of templates derived from etexts
(http://www.gutenberg.org/), you can extract the titles and authors
and put them in a database (assuming the templates have been
compiled into .py template modules):

#def
----


Syntax:

::

    #def METHOD[(ARGUMENTS)]
    #end def

Or the one-line variation:

::

    #def METHOD[(ARGUMENTS)] : TEXT_AND_PLACEHOLDERS

The {#def} directive is used to define new methods in the generated
Python class, or to override superclass methods. It is analogous to
Python's {def} statement. The directive is silent, meaning it does
not itself produce any output. However, the content of the method
will be inserted into the output (and the directives executed)
whenever the method is later called by a $placeholder.

::

    #def myMeth()
    This is the text in my method
    $a $b $c(123)  ## these placeholder names have been defined elsewhere
    #end def

    ## and now use it...
    $myMeth()

The arglist and parentheses can be omitted:

::

    #def myMeth
    This is the text in my method
    $a $b $c(123)
    #end def

    ## and now use it...
    $myMeth

Methods can have arguments and have defaults for those arguments,
just like in Python. Remember the {$} before variable names:

::

    #def myMeth($a, $b=1234)
    This is the text in my method
    $a - $b
    #end def

    ## and now use it...
    $myMeth(1)

The output from this last example will be:

::

    This is the text in my method
    1 - 1234

There is also a single line version of the {#def} directive. {
Unlike the multi-line directives, it uses a colon (:) to delimit
the method signature and body}:

::

    #attr $adj = 'trivial'
    #def myMeth: This is the $adj method
    $myMeth

Leading and trailing whitespace is stripped from the method. This
is in contrast to:

::

    #def myMeth2
    This is the $adj method
    #end def

where the method includes a newline after "method". If you don't
want the newline, add {#slurp}:

::

    #def myMeth3
    This is the $adj method#slurp
    #end def

Because {#def} is handled at compile time, it can appear above or
below the placeholders that call it. And if a superclass
placeholder calls a method that's overridden in a subclass, it's
the subclass method that will be called.

#block ... #end block
---------------------


The {#block} directive allows you to mark a section of your
template that can be selectively reimplemented in a subclass. It is
very useful for changing part of a template without having to
copy-paste-and-edit the entire thing. The output from a template
definition that uses blocks will be identical to the output from
the same template with the {#block ... #end block} tags removed.

({ Note:} don't be confused by the generic word 'block'' in this
Guide, which means a section of code inside { any} {#TAG ... #end
TAG} pair. Thus, an if-block, for-block, def-block, block-block
etc. In this section we are talking only of block-blocks.)

To reimplement the block, use the {#def} directive. The magical
effect is that it appears to go back and change the output text {
at the point the original block was defined} rather than at the
location of the reimplementation.

::

    #block testBlock
    Text in the contents
    area of the block directive
    #if $testIt
    $getFoo()
    #end if
    #end block testBlock

You can repeat the block name in the {#end block} directive or not,
as you wish.

{#block} directives can be nested to any depth.

::

    #block outerBlock
    Outer block contents

    #block innerBlock1
    inner block1 contents
    #end block innerBlock1

    #block innerBlock2
    inner block2 contents
    #end block innerBlock2

    #end block outerBlock

Note that the name of the block is optional for the {#end block}
tag.

Technically, {#block} directive is equivalent to a {#def} directive
followed immediately by a {#placeholder} for the same name. In
fact, that's what Cheetah does. Which means you can use
{$theBlockName} elsewhere in the template to output the block
content again.

There is a one-line {#block} syntax analagous to the one-line
{#def}.

The block must not require arguments because the implicit
placeholder that's generated will call the block without
arguments.


