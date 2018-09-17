.. role:: math(raw)
   :format: html latex

Generating, Caching and Filtering Output
========================================


Output from complex expressions: #echo
--------------------------------------


Syntax:

::

    #echo EXPR

The {#echo} directive is used to echo the output from expressions
that can't be written as simple $placeholders.

::

    Here is my #echo ', '.join(['silly']*5) # example

This produces:

::

    Here is my silly, silly, silly, silly, silly example.

Executing expressions without output: #silent
---------------------------------------------


Syntax:

::

    #silent EXPR

{#silent} is the opposite of {#echo}. It executes an expression but
discards the output.

::

    #silent $myList.reverse()
    #silent $myList.sort()
    Here is #silent $covertOperation() # nothing

If your template requires some Python code to be executed at the
beginning; (e.g., to calculate placeholder values, access a
database, etc), you can put it in a "doEverything" method you
inherit, and call this method using {#silent} at the top of the
template.

One-line #if
------------


Syntax:

::

    #if EXPR1 then EXPR2 else EXPR3#

The {#if} flow-control directive (section flowControl.if) has a
one-line counterpart akin to Perl's and C's {?:} operator. If
{EXPR1} is true, it evaluates {EXPR2} and outputs the result (just
like {#echo EXPR2#}). Otherwise it evaluates {EXPR3} and outputs
that result. This directive is short-circuiting, meaning the
expression that isn't needed isn't evaluated.

You MUST include both 'then' and 'else'. If this doesn't work for
you or you don't like the style use multi-line {#if} directives
(section flowControl.if).

The trailing {#} is the normal end-of-directive character. As usual
it may be omitted if there's nothing after the directive on the
same line.

Caching Output
--------------


Caching individual placeholders
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


By default, the values of each $placeholder is retrieved and
interpolated for every request. However, it's possible to cache the
values of individual placeholders if they don't change very often,
in order to speed up the template filling.

To cache the value of a single {$placeholder}, add an asterisk
after the $; e.g., {$\*var}. The first time the template is filled,
{$var} is looked up. Then whenever the template is filled again,
the cached value is used instead of doing another lookup.

The {$\*} format caches "forever"; that is, as long as the template
instance remains in memory. It's also possible to cache for a
certain time period using the form {$\*<interval>\*variable}, where
{<interval>} is the interval. The time interval can be specified in
seconds (5s), minutes (15m), hours (3h), days (2d) or weeks (1.5w).
The default is minutes.

::

    <HTML>
    <HEAD><TITLE>$title</TITLE></HEAD>
    <BODY>

    $var ${var}           ## dynamic - will be reinterpolated for each request
    $*var2 $*{var2}       ## static - will be interpolated only once at start-up
    $*5*var3 $*5*{var3}   ## timed refresh - will be updated every five minutes.

    </BODY>
    </HTML>

Note that "every five minutes" in the example really means every
five minutes: the variable is looked up again when the time limit
is reached, whether the template is being filled that frequently or
not. Keep this in mind when setting refresh times for CPU-intensive
or I/O intensive operations.

If you're using the long placeholder syntax, ``${}``, the braces go
only around the placeholder name: ``$*.5h*{var.func('arg')}``.

Sometimes it's preferable to explicitly invalidate a cached item
whenever you say so rather than at certain time intervals. You
can't do this with individual placeholders, but you can do it with
cached regions, which will be described next.

Caching entire regions
~~~~~~~~~~~~~~~~~~~~~~


Syntax:

::

    #cache [id=EXPR] [timer=EXPR] [test=EXPR]
    #end cache

The {#cache} directive is used to cache a region of content in a
template. The region is cached as a single unit, after placeholders
and directives inside the region have been evaluated. If there are
any {$\*<interval>\*var} placholders inside the cache region, they
are refreshed only when { both} the cache region { and} the
placeholder are simultaneously due for a refresh.

Caching regions offers more flexibility than caching individual
placeholders. You can specify the refresh interval using a
placeholder or expression, or refresh according to other criteria
rather than a certain time interval.

{#cache} without arguments caches the region statically, the same
way as {$\*var}. The region will not be automatically refreshed.

To refresh the region at an interval, use the {timer=EXPRESSION}
argument, equivalent to {$\*<interval>\*}. The expression should
evaluate to a number or string that is a valid interval (e.g., 0.5,
'3m', etc).

To refresh whenever an expression is true, use {test=EXPRESSION}.
The expression can be a method/function returning true or false, a
boolean placeholder, several of these joined by {and} and/or {or},
or any other expression. If the expression contains spaces, it's
easier to read if you enclose it in {()}, but this is not
required.

To refresh whenever you say so, use {id=EXPRESSION}. Your program
can then call {.refreshCache(ID)} whenever it wishes. This is
useful if the cache depends on some external condition that changes
infrequently but has just changed now.

You can combine arguments by separating them with commas. For
instance, you can specify both {id=} and {interval=}, or {id=} and
{test=}. (You can also combine interval and test although it's not
very useful.) However, repeating an argument is undefined.

::

    #cache
    This is a static cache.  It will not be refreshed.
    $a $b $c
    #end cache

    #cache timer='30m', id='cache1'
    #for $cust in $customers
    $cust.name:
    $cust.street - $cust.city
    #end for
    #end cache

    #cache id='sidebar', test=$isDBUpdated
    ... left sidebar HTML ...
    #end cache

    #cache id='sidebar2', test=($isDBUpdated or $someOtherCondition)
    ... right sidebar HTML ...
    #end cache

The {#cache} directive cannot be nested.

We are planning to add a {'varyBy'} keyword argument in the future
that will allow a separate cache instances to be created for a
variety of conditions, such as different query string parameters or
browser types. This is inspired by ASP.net's varyByParam and
varyByBrowser output caching keywords.

#raw
----


Syntax:

::

    #raw
    #end raw

Any section of a template definition that is inside a {#raw ...
#end raw} tag pair will be printed verbatim without any parsing of
$placeholders or other directives. This can be very useful for
debugging, or for Cheetah examples and tutorials.

{#raw} is conceptually similar to HTML's {<PRE>} tag and LaTeX's {
verbatim{}} tag, but unlike those tags, {#raw} does not cause the
body to appear in a special font or typeface. It can't, because
Cheetah doesn't know what a font is.

#include
--------


Syntax:

::

    #include [raw] FILENAME_EXPR
    #include [raw] source=STRING_EXPR

The {#include} directive is used to include text from outside the
template definition. The text can come from an external file or
from a {$placeholder} variable. When working with external files,
Cheetah will monitor for changes to the included file and update as
necessary.

This example demonstrates its use with external files:

::

    #include "includeFileName.txt"

The content of "includeFileName.txt" will be parsed for Cheetah
syntax.

And this example demonstrates use with {$placeholder} variables:

::

    #include source=$myParseText

The value of {$myParseText} will be parsed for Cheetah syntax. This
is not the same as simply placing the $placeholder tag
"{$myParseText}" in the template definition. In the latter case,
the value of $myParseText would not be parsed.

By default, included text will be parsed for Cheetah tags. The
argument "{raw}" can be used to suppress the parsing.

::

    #include raw "includeFileName.txt"
    #include raw source=$myParseText

Cheetah wraps each chunk of {#include} text inside a nested
{Template} object. Each nested template has a copy of the main
template's searchList. However, {#set} variables are visible across
includes only if the defined using the {#set global} keyword.

All directives must be balanced in the include file. That is, if
you start a {#for} or {#if} block inside the include, you must end
it in the same include. (This is unlike PHP, which allows
unbalanced constructs in include files.)

#slurp
------


Syntax:

::

    #slurp

The {#slurp} directive eats up the trailing newline on the line it
appears in, joining the following line onto the current line.

It is particularly useful in {#for} loops:

::

    #for $i in range(5)
    $i #slurp
    #end for

outputs:

::

    0 1 2 3 4

#indent
-------


This directive is not implemented yet. When/if it's completed, it
will allow you to


#. indent your template definition in a natural way (e.g., the
   bodies of {#if} blocks) without affecting the output

#. add indentation to output lines without encoding it literally in
   the template definition. This will make it easier to use Cheetah to
   produce indented source code programmatically (e.g., Java or Python
   source code).


There is some experimental code that recognizes the {#indent}
directive with options, but the options are purposely undocumented
at this time. So pretend it doesn't exist. If you have a use for
this feature and would like to see it implemented sooner rather
than later, let us know on the mailing list.

The latest specification for the future {#indent} directive is in
the TODO file in the Cheetah source distribution.

Ouput Filtering and #filter
---------------------------


Syntax:

::

    #filter FILTER_CLASS_NAME
    #filter $PLACEHOLDER_TO_A_FILTER_INSTANCE
    #filter None

Output from $placeholders is passed through an ouput filter. The
default filter merely returns a string representation of the
placeholder value, unless the value is {None}, in which case the
filter returns an empty string. Only top-level placeholders invoke
the filter; placeholders inside expressions do not.

Certain filters take optional arguments to modify their behaviour.
To pass arguments, use the long placeholder syntax and precede each
filter argument by a comma. By convention, filter arguments don't
take a {$} prefix, to avoid clutter in the placeholder tag which
already has plenty of dollar signs. For instance, the MaxLen filter
takes an argument 'maxlen':

::

    ${placeholderName, maxlen=20}
    ${functionCall($functionArg), maxlen=$myMaxLen}

To change the output filter, use the {'filter'} keyword to the
{Template} class constructor, or the {#filter} directive at runtime
(details below). You may use {#filter} as often as you wish to
switch between several filters, if certain {$placeholders} need one
filter and other {$placeholders} need another.

The standard filters are in the module {Cheetah.Filters}. Cheetah
currently provides:

    The default filter, which converts None to '' and everything else
    to {str(whateverItIs)}. This is the base class for all other
    filters, and the minimum behaviour for all filters distributed with
    Cheetah.

    Same.

    Same, but truncate the value if it's longer than a certain length.
    Use the 'maxlen' filter argument to specify the length, as in the
    examples above. If you don't specify 'maxlen', the value will not
    be truncated.

    Output a "pageful" of a long string. After the page, output HTML
    hyperlinks to the previous and next pages. This filter uses several
    filter arguments and environmental variables, which have not been
    documented yet.

    Same as default, but convert HTML-sensitive characters
    (':math:`$<$`', '&', ':math:`$>$`') to HTML entities so that the
    browser will display them literally rather than interpreting them
    as HTML tags. This is useful with database values or user input
    that may contain sensitive characters. But if your values contain
    embedded HTML tags you want to preserve, you do not want this
    filter.

    The filter argument 'also' may be used to specify additional
    characters to escape. For instance, say you want to ensure a value
    displays all on one line. Escape all spaces in the value with
    '&nbsp', the non-breaking space:

    ::

        ${$country, also=' '}}


To switch filters using a class object, pass the class using the {
filter} argument to the Template constructor, or via a placeholder
to the {#filter} directive: {#filter $myFilterClass}. The class
must be a subclass of {Cheetah.Filters.Filter}. When passing a
class object, the value of { filtersLib} does not matter, and it
does not matter where the class was defined.

To switch filters by name, pass the name of the class as a string
using the { filter} argument to the Template constructor, or as a
bare word (without quotes) to the {#filter} directive: {#filter
TheFilter}. The class will be looked up in the { filtersLib}.

The filtersLib is a module containing filter classes, by default
{Cheetah.Filters}. All classes in the module that are subclasses of
{Cheetah.Filters.Filter} are considered filters. If your filters
are in another module, pass the module object as the { filtersLib}
argument to the Template constructor.

Writing a custom filter is easy: just override the {.filter}
method.

::

        def filter(self, val, **kw):     # Returns a string.

Return the { string} that should be output for 'val'. 'val' may be
any type. Most filters return \`' for {None}. Cheetah passes one
keyword argument: ``kw['rawExpr']`` is the placeholder name as it
appears in the template definition, including all subscripts and
arguments. If you use the long placeholder syntax, any options you
pass appear as keyword arguments. Again, the return value must be a
string.

You can always switch back to the default filter this way: {#filter
None}. This is easy to remember because "no filter" means the
default filter, and because None happens to be the only object the
default filter treats specially.

We are considering additional filters; see
http://webware.colorstudy.net/twiki/bin/view/Cheetah/MoreFilters
for the latest ideas.


