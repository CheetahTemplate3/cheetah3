Security
========


A template is code
------------------


Cheetah compiles a template into a Python module and then runs it.
A placeholder is a Python expression, so a template can do anything
Python can do:

::

    >>> from Cheetah.Template import Template
    >>> print(Template('$__import__("os").popen("id").read()'))
    uid=1000(user) gid=1000(user) groups=1000(user)

Template definitions are source code and need the same trust as the
rest of your program. Do not compile or render a template whose text
comes from a user, an upload, a request parameter or any other place
you do not control. Doing so is remote code execution.


Where user input belongs
------------------------


Pass user input to the template instead of into it:

::

    # Wrong. The user writes the program.
    print(Template(user_input))

    # Right. The user fills a placeholder.
    print(Template('Hello $name', searchList=[{'name': user_input}]))

Values in the searchList are looked up and written out, never
compiled. They still reach the output verbatim, so filter them for
the output format you generate; see the ``#filter`` directive and the
WebSafe filter for HTML.


There is no sandbox
-------------------


Compiler settings restrict the template language, not what a template
is allowed to do. The example above runs unchanged with
``useNameMapper=False`` and with every directive listed in
``disabledDirectives``, because none of that touches the placeholder
expression. Treat these settings as a way to keep templates simple,
not as a security boundary.

Cheetah does not offer a safe mode. Restricting Python expressions to
a safe subset inside the same interpreter has a long history of
escapes. If you have to render
templates you do not control, isolate the whole process: a separate
user account, a container, seccomp, or a jail, with the limits set
outside of Python.
