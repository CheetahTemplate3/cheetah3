Tips, Tricks and Troubleshooting
================================


This chapter contains short stuff that doesn't fit anywhere else.

See the Cheetah FAQ for more specialized issues and for
troubleshooting tips. Check the wiki periodically for recent tips
contributed by users. If you get stuck and none of these resources
help, ask on the mailing list.

Placeholder Tips
----------------


Here's how to do certain important lookups that may not be obvious.
For each, we show first the Cheetah expression and then the Python
equivalent, because you can use these either in templates or in
pure Python subclasses. The Cheetah examples use NameMapper
shortcuts (uniform dotted notation, autocalling) as much as
possible.

To verify whether a variable exists in the searchList:

::

    $varExists('theVariable')
    self.varExists('theVariable')

This is useful in {#if} or {#unless} constructs to avoid a
{#NameMapper.NotFound} error if the variable doesn't exist. For
instance, a CGI GET parameter that is normally supplied but in this
case the user typed the URL by hand and forgot the parameter (or
didn't know about it). ({.hasVar} is a synonym for {.varExists}.)

To look up a variable in the searchList from a Python method:

::

    self.getVar('theVariable')
    self.getVar('theVariable', myDefault)

This is the equivalent to {$theVariable} in the template. If the
variable is missing, it returns the second argument, {myDefault},
if present, or raises {NameMapper.NotFound} if there is no second
argument. However, it usually easier to write your method so that
all needed searchList values come in as method arguments. That way
the caller can just use a {$placeholder} to specify the argument,
which is less verbose than you writing a getVar call.

To do a "safe" placeholder lookup that returns a default value if
the variable is missing:

::

    $getVar('theVariable', None)
    $getVar('theVariable', $myDefault)

To get an environmental variable, put {os.environ} on the
searchList as a container. Or read the envvar in Python code and
set a placeholder variable for it.

Remember that variables found earlier in the searchList override
same-name variables located in a later searchList object. Be
careful when adding objects containing other variables besides the
ones you want (e.g., {os.environ}, CGI parameters). The "other"
variables may override variables your application depends on,
leading to hard-to-find bugs. Also, users can inadvertently or
maliciously set an environmental variable or CGI parameter you
didn't expect, screwing up your program. To avoid all this, know
what your namespaces contain, and place the namespaces you have the
most control over first. For namespaces that could contain
user-supplied "other" variables, don't put the namespace itself in
the searchList; instead, copy the needed variables into your own
"safe" namespace.

Diagnostic Output
-----------------


If you need send yourself some debugging output, you can use
{#silent} to output it to standard error:

::

    #silent $sys.stderr.write("Incorrigible var is '$incorrigible'.\n")
    #silent $sys.stderr.write("Is 'unknown' in the searchList? " +
        $getVar("unknown", "No.") + "\n" )


When to use Python methods
--------------------------


You always have a choice whether to code your methods as Cheetah
{#def} methods or Python methods (the Python methods being located
in a class your template inherits). So how do you choose?

Generally, if the method consists mostly of text and placeholders,
use a Cheetah method (a {#def} method). That's why {#def} exists,
to take the tedium out of writing those kinds of methods. And if
you have a couple {#if} stanzas to {#set} some variables, followed
by a {#for} loop, no big deal. But if your method consists mostly
of directives and only a little text, you're better off writing it
in Python. Especially be on the watch for extensive use of {#set},
{#echo} and {#silent} in a Cheetah method-it's a sure sign you're
probably using the wrong language. Of course, though, you are free
to do so if you wish.

Another thing that's harder to do in Cheetah is adjacent or nested
multiline stanzas (all those directives with an accompanying {#end}
directive). Python uses indentation to show the beginning and end
of nested stanzas, but Cheetah can't do that because any
indentation shows up in the output, which may not be desired. So
unless all those extra spaces and tabs in the output are
acceptable, you have to keep directives flush with the left margin
or the preceding text.

The most difficult decisions come when you have conflicting goals.
What if a method generates its output in parts (i.e., output
concatenation), contains many searchList placeholders and lots of
text, { and} requires lots of {#if ... #set ... #else #set ... #end
if} stanzas. A Cheetah method would be more advantageous in some
ways, but a Python method in others. You'll just have to choose,
perhaps coding groups of methods all the same way. Or maybe you can
split your method into two, one Cheetah and one Python, and have
one method call the other. Usually this means the Cheetah method
calling the Python method to calculate the needed values, then the
Cheetah method produces the output. One snag you might run into
though is that {#set} currently can set only one variable per
statement, so if your Python method needs to return multiple values
to your Cheetah method, you'll have to do it another way.

Calling superclass methods, and why you have to
-----------------------------------------------


If your template or pure Python class overrides a standard method
or attribute of {Template} or one of its base classes, you should
call the superclass method in your method to prevent various things
from breaking. The most common methods to override are {.awake} and
{.\_\_init\_\_}. {.awake} is called automatically by Webware early
during the web transaction, so it makes a convenient place to put
Python initialization code your template needs. You'll definitely
want to call the superclass {.awake} because it sets up many
wonderful attributes and methods, such as those to access the CGI
input fields.

There's nothing Cheetah-specific to calling superclass methods, but
because it's vital, we'll recap the standard Python techniques
here. We mention only the solution for old-style classes because
Cheetah classes are old-style (in other Python documentation, you
will find the technique for new-style classes, but they are not
listed here because they cannot be used with Cheetah if you use
dynamically-compiled templates).

::

    from Cheetah.Template import Template
    class MyClass(Template):
        def awake(self, trans):
            Template.awake(self, trans)
            ... great and exciting features written by me ...

[ @@MO: Need to test this. .awake is in Servlet, which is a
superclass of Template. Do we really need both imports? Can we call
Template.awake? ]

To avoid hardcoding the superclass name, you can use this function
{callbase()}, which emulates {super()} for older versions of
Python. It also works even {super()} does exist, so you don't have
to change your servlets immediately when upgrading. Note that the
argument sequence is different than {super} uses.

::

    ===========================================================================
    # Place this in a module SOMEWHERE.py .  Contributed by Edmund Lian.
    class CallbaseError(AttributeError):
        pass

    def callbase(obj, base, methodname='__init__', args=(), kw={},
        raiseIfMissing=None):
        try: method = getattr(base, methodname)
        except AttributeError:
            if raiseIfMissing:
                raise CallbaseError, methodname
            return None
        if args is None: args = ()
        return method(obj, *args, **kw)
    ===========================================================================
    # Place this in your class that's overriding .awake (or any method).
    from SOMEWHERE import callbase
    class MyMixin:
            def awake(self, trans):
                    args = (trans,)
                    callbase(self, MyMixin, 'awake', args)
                    ... everything else you want to do ...
    ===========================================================================

All methods
-----------


Here is a list of all the standard methods and attributes that can
be accessed from a placeholder. Some of them exist for you to call,
others are mainly used by Cheetah internally but you can call them
if you wish, and others are only for internal use by Cheetah or
Webware. Do not use these method names in mixin classes
({#extends}, section inheritanceEtc.extends) unless you intend to
override the standard method.

Variables with a star prefix ({ \*}) are frequently used in
templates or in pure Python classes.

\*{Inherited from Cheetah.Template}

    Compile the template. Automatically called by {.\_\_init\_\_}.

    Return the module code the compiler generated, or {None} if no
    compilation took place.

    Return the class code the compiler generated, or {None} if no
    compilation took place.

    Return a reference to the underlying search list. (a list of
    objects). Use this to print out your searchList for debugging.
    Modifying the returned list will affect your placeholder searches!

    Return a reference to the current error catcher.

    If 'cacheKey' is not {None}, refresh that item in the cache. If
    {None}, delete all items in the cache so they will be recalculated
    the next time they are encountered.

    Break reference cycles before discarding a servlet.

    Look up a variable in the searchList. Same as {$varName} but allows
    you to specify a default value and control whether autocalling
    occurs.

    Read the named file. If used as a placeholder, inserts the file's
    contents in the output without interpretation, like {#include raw}.
    If used in an expression, returns the file's content (e.g., to
    assign it to a variable).

    This is what happens if you run a .py template module as a
    standalone program.


\*{Inherited from Cheetah.Utils.WebInputMixin}

    Exception raised by {.webInput}.

    Convenience method to access GET/POST variables from a Webware
    servlet or CGI script, or Webware cookie or session variables. See
    section webware.webInput for usage information.


\*{Inherited from Cheetah.SettingsManager}

    Get a compiler setting.

    Does this compiler setting exist?

    Set setting 'name' to 'value'. See {#compiler-settings}, section
    parserInstructions.compiler-settings.

    Return the underlying settings dictionary. (Warning: modifying this
    dictionary will change Cheetah's behavior.)

    Return a copy of the underlying settings dictionary.

    Return a deep copy of the underlying settings dictionary. See
    Python's {copy} module.

    Update Cheetah's compiler settings from the 'newSettings'
    dictionary. If 'merge' is true, update only the names in
    newSettings and leave the other names alone. (The SettingsManager
    is smart enough to update nested dictionaries one key at a time
    rather than overwriting the entire old dictionary.) If 'merge' is
    false, delete all existing settings so that the new ones are the
    only settings.

    Same, but pass a string of {name=value} pairs rather than a
    dictionary, the same as you would provide in a {#compiler-settings}
    directive, section parserInstructions.compiler-settings.

    Same, but exec a Python source file and use the variables it
    contains as the new settings. (e.g.,
    {cheetahVarStartToken = "@"}).

    Same, but get the new settings from a text file in ConfigParser
    format (similar to Windows' \*.ini file format). See Python's
    {ConfigParser} module.

    Same, but read the open file object 'inFile' for the new settings.

    Same, but read the new settings from a string in ConfigParser
    format.

    Write the current compiler settings to a file named 'path' in
    \*.ini format.

    Return a string containing the current compiler settings in \*.ini
    format.


\*{Inherited from Cheetah.Servlet}

{ Do not override these in a subclass or assign to them as
attributes if your template will be used as a servlet,} otherwise
Webware will behave unpredictably. However, it { is} OK to put
same-name variables in the searchList, because Webware does not use
the searchList.

EXCEPTION: It's OK to override { awake} and { sleep} as long as you
call the superclass methods. (See section
tips.callingSuperclassMethods.)

    True if this template instance is part of a live transaction in a
    running WebKit servlet.

    True if Webware is installed and the template instance inherits
    from WebKit.Servlet. If not, it inherits from
    Cheetah.Servlet.DummyServlet.

    Called by WebKit at the beginning of the web transaction.

    Called by WebKit at the end of the web transaction.

    Called by WebKit to produce the web transaction content. For a
    template-servlet, this means filling the template.

    Break reference cycles before deleting instance.

    The filesystem pathname of the template-servlet (as opposed to the
    URL path).

    The current Webware transaction.

    The current Webware application.

    The current Webware response.

    The current Webware request.

    The current Webware session.

    Call this method to insert text in the filled template output.


Several other goodies are available to template-servlets under the
{request} attribute, see section webware.input.

{transaction}, {response}, {request} and {session} are created from
the current transaction when WebKit calls {awake}, and don't exist
otherwise. Calling {awake} yourself (rather than letting WebKit
call it) will raise an exception because the {transaction} argument
won't have the right attributes.

\*{Inherited from WebKit.Servlet} These are accessible only if
Cheetah knows Webware is installed. This listing is based on a CVS
snapshot of Webware dated 22 September 2002, and may not include
more recent changes.

The same caveats about overriding these methods apply.

    The simple name of the class. Used by Webware's logging and
    debugging routines.

    Used by Webware's logging and debugging routines.

    True if the servlet can be multithreaded.

    True if the servlet can be used for another transaction after the
    current transaction is finished.

    Depreciated by {.serverSidePath()}.


Optimizing templates
--------------------


Here are some things you can do to make your templates fill faster
and user fewer CPU cycles. Before you put a lot of energy into
this, however, make sure you really need to. In many situations,
templates appear to initialize and fill instantaneously, so no
optimization is necessary. If you do find a situation where your
templates are filling slowly or taking too much memory or too many
CPU cycles, we'd like to hear about it on the mailing list.

Cache $placeholders whose values don't change frequently. (Section
output.caching).

Use {#set} for values that are very frequently used, especially if
they come out of an expensive operation like a
deeply.nested.structure or a database lookup. {#set} variables are
set to Python local variables, which have a faster lookup time than
Python globals or values from Cheetah's searchList.

Moving variable lookups into Python code may provide a speedup in
certain circumstances. If you're just reading {self} attributes,
there's no reason to use NameMapper lookup ($placeholders) for
them. NameMapper does a lot more work than simply looking up a
{self} attribute.

On the other hand, if you don't know exactly where the value will
come from (maybe from {self}, maybe from the searchList, maybe from
a CGI input variable, etc), it's easier to just make that an
argument to your method, and then the template can handle all the
NameMapper lookups for you:

::

    #silent $myMethod($arg1, $arg2, $arg3)

Otherwise you'd have to call {self.getVar('arg1')} etc in your
method, which is more wordy, and tedious.

PSP-style tags
--------------


{<%= ... %>} and {<% ... %>} allow an escape to Python syntax
inside the template. You do not need it to use Cheetah effectively,
and we're hard pressed to think of a case to recommend it.
Nevertheless, it's there in case you encounter a situation you
can't express adequately in Cheetah syntax. For instance, to set a
local variable to an elaborate initializer.

{<%= ... %>} encloses a Python expression whose result will be
printed in the output.

{<% ... %>} encloses a Python statement or expression (or set of
statements or expressions) that will be included as-is into the
generated method. The statements themselves won't produce any
output, but you can use the local function {write(EXPRESSION)} to
produce your own output. (Actually, it's a method of a file-like
object, but it looks like a local function.) This syntax also may
be used to set a local variable with a complicated initializer.

To access Cheetah services, you must use Python code like you would
in an inherited Python class. For instance, use {self.getVar()} to
look up something in the searchList.

{ Warning:} { No error checking is done!} If you write:

::

    <% break %>      ## Wrong!

you'll get a {SyntaxError} when you fill the template, but that's
what you deserve.

Note that these are PSP-{ style} tags, not PSP tags. A Cheetah
template is not a PSP document, and you can't use PSP commands in
it.

Calling one template from another
---------------------------------

Cheetah templates are really python modules in disguise. I.e., when
Cheetah loads a template it compiles it to python code and then to byte
code. Every template is compiled as a single class. The thing is,
neither the source code nor byte code are saved to files automatically.

There are a few ways to allow a user to import one template (python
module!) from another.

1. A user can compile templates to `*.py` files using `cheetah compile`
command line program. Then import works at the Python level.

To semi-automatically compile all templates after editing them one can
use the following `Makefile` (GNU flavour)::

	.SUFFIXES: # Clear the suffix list
	.SUFFIXES: .py .tmpl

	%.py: %.tmpl
		cheetah compile --nobackup $<
		python -m compile $@

	templates = $(shell echo \*.tmpl)
	modules = $(patsubst %.tmpl,%.py,$(templates))

	.PHONY: all
	all: $(modules)

(Don't forget - makefiles require indent with tabs, not spaces.)

2. Subvert Python import to make Cheetah import directly from `*.tmpl`
files using `import hooks <../api/Cheetah.ImportHooks.html>`_.

Example code::

    from Cheetah import ImportHooks
    ImportHooks.install()

    import sys
    sys.path.insert(0, 'path/to/template_dir')  # or sys.path.append

ImportHooks try to import from `*.pyc`, `*.py` and `*.tmpl` - whatever
is found first. ImportHooks automatically compile `*.tmpl` to `*.py` and
`*.pyc`.

Makefiles
---------


If your project has several templates and you get sick of typing
"cheetah compile FILENAME.tmpl" all the time-much less remembering
which commands to type when-and your system has the {make} command
available, consider building a Makefile to make your life easier.

Here's a simple Makefile that controls two templates,
ErrorsTemplate and InquiryTemplate. Two external commands,
{inquiry} and {receive}, depend on ErrorsTemplate.py. Aditionally,
InquiryTemplate itself depends on ErrorsTemplate.

::

    all:  inquiry  receive

    .PHONY:  all  receive  inquiry  printsource

    printsource:
            a2ps InquiryTemplate.tmpl ErrorsTemplate.tmpl

    ErrorsTemplate.py:  ErrorsTemplate.tmpl
            cheetah compile ErrorsTemplate.tmpl

    InquiryTemplate.py:  InquiryTemplate.tmpl ErrorsTemplate.py
            cheetah compile InquiryTemplate.tmpl

    inquiry: InquiryTemplate.py  ErrorsTemplate.py

    receive: ErrorsTemplate.py

Now you can type {make} anytime and it will recompile all the
templates that have changed, while ignoring the ones that haven't.
Or you can recompile all the templates {receive} needs by typing
{make receive}. Or you can recompile only ErrorsTemplate by typing
{make ErrorsTemplate}. There's also another target, "printsource":
this sends a Postscript version of the project's source files to
the printer. The .PHONY target is explained in the {make}
documentation; essentially, you have it depend on every target that
doesn't produce an output file with the same name as the target.

Using Cheetah in a Multi-Threaded Application
---------------------------------------------


Template classes may be shared freely between threads. However,
template instances should not be shared unless you either:


-  Use a lock (mutex) to serialize template fills, to prevent two
   threads from filling the template at the same time.

-  Avoid thread-unsafe features:


   -  Modifying searchList values or instance variables.

   -  Caching ({$\*var}, {#cache}, etc).

   -  {#set global}, {#filter}, {#errorCatcher}.


   Any changes to these in one thread will be visible in other
   threads, causing them to give inconsistent output.


About the only advantage in sharing a template instance is building
up the placeholder cache. But template instances are so low
overhead that it probably wouldn't take perceptibly longer to let
each thread instantiate its own template instance. Only if you're
filling templates several times a second would the time difference
be significant, or if some of the placeholders trigger extremely
slow calculations (e.g., parsing a long text file each time). The
biggest overhead in Cheetah is importing the {Template} module in
the first place, but that has to be done only once in a
long-running application.

You can use Python's {mutex} module for the lock, or any similar
mutex. If you have to change searchList values or instance
variables before each fill (which is usually the case), lock the
mutex before doing this, and unlock it only after the fill is
complete.

For Webware servlets, you're probably better off using Webware's
servlet caching rather than Cheetah's caching. Don't override the
servlet's {.canBeThreaded()} method unless you avoid the unsafe
operations listed above.

Using Cheetah with gettext
--------------------------


{ gettext} is a project for creating internationalized
applications. For more details, visit
http://docs.python.org/lib/module-gettext.html. gettext can be used
with Cheetah to create internationalized applications, even for CJK
character sets, but you must keep a couple things in mind:


-  xgettext is used on compiled templates, not on the templates
   themselves.

-  The way the NameMapper syntax gets compiled to Python gets in
   the way of the syntax that xgettext recognizes. Hence, a special
   case exists for the functions {\_}, {N\_}, and {ngettext}. If you
   need to use a different set of functions for marking strings for
   translation, you must set the Cheetah setting {gettextTokens} to a
   list of strings representing the names of the functions you are
   using to mark strings for translation.



