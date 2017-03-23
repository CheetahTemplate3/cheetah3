Precompiled Templates
=====================

Why bother?
-----------
Since Cheetah supports two basic modes: dynamic and precompiled templates, you have
a lot of options when it comes to utilizing Cheetah, particularly in web environments.

There is added speed to be gained by using pre-compiled templates, especially when
using mod_python with Apache. Precompiling your templates means Apache/mod_python
can load your template's generated module into memory and then execution is only
limited by the speed of the Python being executed, and not the Cheetah compiler.
You can further optimize things by then pre-compiling the generated Python files
(.py) down to Python byte-code (.pyc) so save cycles interpreting the Python.


Basic Pre-compilation
---------------------
Suppose you have a template that looks something like this::

    #attr title = "This is my Template"
    <html>
        <head>
            <title>\${title}</title>
        </head>
        <body>
            Hello \${who}!
        </body>
    </html>
**Figure 1. hello.tmpl**

In order to compile this down to a Python file, you need to only execute the
`cheetah compile hello.tmpl` command. The results will be a Python file (.py)
which you can then treat as any other Python module in your code base.


Importing and lookup
--------------------
Typically for the template in *Figure 1*, I could easily import it post-compilation
as any other Python module::

    from templates import hello

    def myMethod():
        tmpl = hello.hello(searchList=[{'who' : 'world'}])
        results = tmpl.respond()

**Figure 2. runner.py**

*Note:* If you use the `\#implements` directive, `respond` may not be your "main
method" for executing the Cheetah template. You can adjust the example above in
*Figure 2* by using `getattr()` to make the lookup of the main method dynamic::

    def myMethod():
        tmpl = hello.hello(searchList=[{'who' : 'world'}])
        mainMethod = getattr(tmpl, '_mainCheetahMethod_for_%s' % tmpl.__class__.__name__)
        results = getattr(tmpl, mainMethod)()

**Figure 3. Dynamic runner.py**
