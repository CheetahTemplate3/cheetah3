Instructions to the Parser/Compiler
===================================


#breakpoint
-----------


Syntax:

::

    #breakpoint

{#breakpoint} is a debugging tool that tells the parser to stop
parsing at a specific point. All source code from that point on
will be ignored.

The difference between {#breakpoint} and {#stop} is that {#stop}
occurs in normal templates (e.g., inside an {#if}) but
{#breakpoint} is used only when debugging Cheetah. Another
difference is that {#breakpoint} operates at compile time, while
{#stop} is executed at run time while filling the template.

#compiler-settings
------------------


Syntax:

::

    #compiler-settings
    key = value    (no quotes)
    #end compiler-settings

    #compiler-settings reset

The {#compiler-settings} directive overrides Cheetah's standard
settings, changing how it parses source code and generates Python
code. This makes it possible to change the behaviour of Cheetah's
parser/compiler for a certain template, or within a portion of the
template.

The {reset} argument reverts to the default settings. With {reset},
there's no end tag.

Here are some examples of what you can do:

::

    $myVar
    #compiler-settings
    cheetahVarStartToken = @
    #end compiler-settings
    @myVar
    #compiler-settings reset
    $myVar

::

    ## normal comment
    #compiler-settings
    commentStartToken = //
    #end compiler-settings

    // new style of comment

    #compiler-settings reset

    ## back to normal comments

::

    #slurp
    #compiler-settings
    directiveStartToken = %
    #end compiler-settings

    %slurp
    %compiler-settings reset

    #slurp

Here's a partial list of the settings you can change:


#. syntax settings


   #. cheetahVarStartToken

   #. commentStartToken

   #. multilineCommentStartToken

   #. multilineCommentEndToken

   #. directiveStartToken

   #. directiveEndToken


#. code generation settings


   #. commentOffset

   #. outputRowColComments

   #. defDocStrMsg

   #. useNameMapper

   #. useAutocalling

   #. reprShortStrConstants

   #. reprNewlineThreshold



The meaning of these settings and their default values will be
documented in the future.


