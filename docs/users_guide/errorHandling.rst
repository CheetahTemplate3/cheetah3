Error Handling
==============


There are two ways to handle runtime errors (exceptions) in
Cheetah. The first is with the Cheetah directives that mirror
Python's structured exception handling statements. The second is
with Cheetah's {ErrorCatcher} framework. These are described
below.

#try ... #except ... #end try, #finally, and #assert
----------------------------------------------------


Cheetah's exception-handling directives are exact mirrors Python's
exception-handling statements. See Python's documentation for
details. The following Cheetah code demonstrates their use:

::

    #try
      $mightFail()
    #except
      It failed
    #end try

    #try
      #assert $x == $y
    #except AssertionError
      They're not the same!
    #end try

    #try
      #raise ValueError
    #except ValueError
      #pass
    #end try


    #try
      $mightFail()
    #except ValueError
      Hey, it raised a ValueError!
    #except NameMapper.NotFound
      Hey, it raised a NameMapper.NotFound!
    #else
      It didn't raise anything!
    #end try

    #try
      $mightFail()
    #finally
      $cleanup()
    #end try

Like Python, {#except} and {#finally} cannot appear in the same
try-block, but can appear in nested try-blocks.

#errorCatcher and ErrorCatcher objects
--------------------------------------


Syntax:

::

    #errorCatcher CLASS
    #errorCatcher $PLACEHOLDER_TO_AN_ERROR_CATCHER_INSTANCE

{ErrorCatcher} is a debugging tool that catches exceptions that
occur inside {$placeholder} tags and provides a customizable
warning to the developer. Normally, the first missing namespace
value raises a {NameMapper.NotFound} error and halts the filling of
the template. This requires the developer to resolve the exceptions
in order without seeing the subsequent output. When an
{ErrorCatcher} is enabled, the developer can see all the exceptions
at once as well as the template output around them.

The {Cheetah.ErrorCatchers} module defines the base class for
ErrorCatchers:

::

    class ErrorCatcher:
        _exceptionsToCatch = (NameMapper.NotFound,)

        def __init__(self, templateObj):
            pass

        def exceptions(self):
            return self._exceptionsToCatch

        def warn(self, exc_val, code, rawCode, lineCol):
            return rawCode

This ErrorCatcher catches {NameMapper.NotFound} exceptions and
leaves the offending placeholder visible in its raw form in the
template output. If the following template is executed:

::

    #errorCatcher Echo
    #set $iExist = 'Here I am!'
    Here's a good placeholder: $iExist
    Here's bad placeholder: $iDontExist

the output will be:

::

    Here's a good placeholder: Here I am!
    Here's bad placeholder: $iDontExist

The base class shown above is also accessible under the alias
{Cheetah.ErrorCatchers.Echo}. {Cheetah.ErrorCatchers} also provides
a number of specialized subclasses that warn about exceptions in
different ways. {Cheetah.ErrorCatchers.BigEcho} will output

::

    Here's a good placeholder: Here I am!
    Here's bad placeholder: ===============&lt;$iDontExist could not be found&gt;===============

ErrorCatcher has a significant performance impact and is turned off
by default. It can also be turned on with the {Template} class'
{'errorCatcher'} keyword argument. The value of this argument
should either be a string specifying which of the classes in
{Cheetah.ErrorCatchers} to use, or a class that subclasses
{Cheetah.ErrorCatchers.ErrorCatcher}. The {#errorCatcher} directive
can also be used to change the errorCatcher part way through a
template.

{Cheetah.ErrorCatchers.ListErrors} will produce the same output as
{Echo} while maintaining a list of the errors that can be retrieved
later. To retrieve the list, use the {Template} class'
{'errorCatcher'} method to retrieve the errorCatcher and then call
its {listErrors} method.

ErrorCatcher doesn't catch exceptions raised inside directives.


