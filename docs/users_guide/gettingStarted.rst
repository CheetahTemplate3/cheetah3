Getting Started
===============


Requirements
------------


Cheetah requires Python release 2.7 (there are plans to support 3.4+).
It is known to run on Linux, Windows, FreeBSD and Solaris,
and should run anywhere Python runs.

99% of Cheetah is written in Python. There is one small C module
({\_namemapper.so}) for speed, but Cheetah automatically falls back
to a Python equivalent ({NameMapper.py}) if the C module is not
available.

Cheetah can use an additional module Markdown but it's not strictly required.

Installation
------------


To install Cheetah in your system-wide Python library:


#. Login as a user with privileges to install system-wide Python
   packages. On POSIX systems (AIX, Solaris, Linux, IRIX, etc.), the
   command is normally 'su root'. On non-POSIX systems such as Windows
   NT, login as an administrator.

#. Run {pip install CT3} at the command prompt.

#. Or download source code and run {python setup.py install}.

#. The setup program will install the wrapper script { cheetah} to
   wherever it usually puts Python binaries ("/usr/bin/", "bin/" in
   the Python install directory, etc.)

#. If you cannot login as as an administrator install Cheetah as user to your
   own home directory: add option {--user} to commands: either
   {pip install --user CT3} or {python setup.py install --user}.

Cheetah's installation is managed by Python's Distribution
Utilities ('distutils'). There are many options for customization.
Type {python setup.py help} for more information.

To install Cheetah in an alternate location - someplace outside
Python's {site-packages/} directory, use one of these options:

::

        python setup.py install --home /home/tavis
        python setup.py install --install-lib /home/tavis/lib/python

Either way installs to /home/tavis/lib/python/Cheetah/ . Of course,
/home/tavis/lib/python must be in your Python path in order for
Python to find Cheetah.

Files
-----


If you do the systemwide install, all Cheetah modules are installed
in the { site-packages/Cheetah/} subdirectory of your standard
library directory; e.g.,
/opt/Python2.2/lib/python2.2/site-packages/Cheetah.

Two commands are installed in Python's {bin/} directory or a system
bin directory: {cheetah} (section gettingStarted.cheetah) and
{cheetah-compile} (section howWorks.cheetah-compile).

Uninstalling
------------


To uninstall Cheetah, merely delete the site-packages/Cheetah/
directory. Then delete the "cheetah" and "cheetah-compile" commands
from whichever bin/ directory they were put in.

The 'cheetah' command
---------------------


Cheetah comes with a utility {cheetah} that provides a command-line
interface to various housekeeping tasks. The command's first
argument is the name of the task. The following commands are
currently supported:

::

    cheetah compile [options] [FILES ...]     : Compile template definitions
    cheetah fill [options] [FILES ...]        : Fill template definitions
    cheetah help                              : Print this help message
    cheetah options                           : Print options help message
    cheetah test                              : Run Cheetah's regression tests
    cheetah version                           : Print Cheetah version number

You only have to type the first letter of the command: {cheetah c}
is the same as {cheetah compile}.

The test suite is described in the next section. The {compile}
command will be described in section howWorks.cheetah-compile, and
the {fill} command in section howWorks.cheetah-fill.

The depreciated {cheetah-compile} program does the same thing as
{cheetah compile}.

Testing your installation
-------------------------


After installing Cheetah, you can run its self-test routine to
verify it's working properly on your system. Change directory to
any directory you have write permission in (the tests write
temporary files). Do not run the tests in the directory you
installed Cheetah from, or you'll get unnecessary errors. Type the
following at the command prompt:

::

    cheetah test

The tests will run for about three minutes and print a
success/failure message. If the tests pass, start Python in
interactive mode and try the example in the next section.

Certain test failures are insignificant:

    Certain tests run "cheetah" as a subcommand. The failure may mean
    the command wasn't found in your system path. (What happens if you
    run "cheetah" on the command line?) The failure also happens on
    some Windows systems for unknown reasons. This failure has never
    been observed outside the test suite. Long term, we plan to rewrite
    the tests to do a function call rather than a subcommand, which
    will also make the tests run significantly faster.

    The test tried to write a temporary module in the current directory
    and {import} it. Reread the first paragraph in this section about
    the current directory.

    May be the same problem as SampleBaseClass; let us know if changing
    the current directory doesn't work.


If any other tests fail, please send a message to the e-mail list
with a copy of the test output and the following details about your
installation:


#. your version of Cheetah

#. your version of Python

#. your operating system

#. whether you have changed anything in the Cheetah installation


Quickstart tutorial
-------------------


This tutorial briefly introduces how to use Cheetah from the Python
prompt. The following chapters will discuss other ways to use
templates and more of Cheetah's features.

The core of Cheetah is the {Template} class in the
{Cheetah.Template} module. The following example shows how to use
the {Template} class in an interactive Python session. {t} is the
Template instance. Lines prefixed with {>>>} and {...} are user
input. The remaining lines are Python output.

::

    >>> from Cheetah.Template import Template
    >>> templateDef = """
    ... <HTML>
    ... <HEAD><TITLE>$title</TITLE></HEAD>
    ... <BODY>
    ... $contents
    ... ## this is a single-line Cheetah comment and won't appear in the output
    ... #* This is a multi-line comment and won't appear in the output
    ...    blah, blah, blah
    ... *#
    ... </BODY>
    ... </HTML>"""
    >>> nameSpace = {'title': 'Hello World Example', 'contents': 'Hello World!'}
    >>> t = Template(templateDef, searchList=[nameSpace])
    >>> print t

    <HTML>
    <HEAD><TITLE>Hello World Example</TITLE></HEAD>
    <BODY>
    Hello World!
    </BODY>
    </HTML>
    >>> print t    # print it as many times as you want
          [ ... same output as above ... ]
    >>> nameSpace['title'] = 'Example #2'
    >>> nameSpace['contents'] = 'Hiya Planet Earth!'
    >>> print t   # Now with different plug-in values.
    <HTML>
    <HEAD><TITLE>Example #2</TITLE></HEAD>
    <BODY>
    Hiya Planet Earth!
    </BODY>
    </HTML>

Since Cheetah is extremely flexible, you can achieve the same
result this way:

::

    >>> t2 = Template(templateDef)
    >>> t2.title = 'Hello World Example!'
    >>> t2.contents = 'Hello World'
    >>> print t2
          [ ... same output as the first example above ... ]
    >>> t2.title = 'Example #2'
    >>> t2.contents = 'Hello World!'
    >>> print t2
         [ ... same as Example #2 above ... ]

Or this way:

::

    >>> class Template3(Template):
    >>>     title = 'Hello World Example!'
    >>>     contents = 'Hello World!'
    >>> t3 = Template3(templateDef)
    >>> print t3
         [ ... you get the picture ... ]

The template definition can also come from a file instead of a
string, as we will see in section howWorks.constructing.

The above is all fine for short templates, but for long templates
or for an application that depends on many templates in a
hierarchy, it's easier to store the templates in separate \*.tmpl
files and use the { cheetah compile} program to convert them into
Python classes in their own modules. This will be covered in
section howWorks.cheetah-compile.

As an appetizer, we'll just briefly mention that you can store
constant values { inside} the template definition, and they will be
converted to attributes in the generated class. You can also create
methods the same way. You can even use inheritance to arrange your
templates in a hierarchy, with more specific templates overriding
certain parts of more general templates (e.g., a "page" template
overriding a sidebar in a "section" template).

For the minimalists out there, here's a template definition,
instantiation and filling all in one Python statement:

::

    >>> print Template("Templates are pretty useless without placeholders.")
    Templates are pretty useless without placeholders.

You use a precompiled template the same way, except you don't
provide a template definition since it was already established:

::

    from MyPrecompiledTemplate import MyPrecompiledTemplate
    t = MyPrecompiledTemplate()
    t.name = "Fred Flintstone"
    t.city = "Bedrock City"
    print t


