Comments
========


Comments are used to mark notes, explanations, and decorative text
that should not appear in the output. Cheetah maintains the
comments in the Python module it generates from the Cheetah source
code. There are two forms of the comment directive: single-line and
multi-line.

All text in a template definition that lies between two hash
characters ({##}) and the end of the line is treated as a
single-line comment and will not show up in the output, unless the
two hash characters are escaped with a backslash.

::

    ##=============================  this is a decorative comment-bar
    $var    ## this is an end-of-line comment
    ##=============================

Any text between {#\*} and {\*#} will be treated as a multi-line
comment.

::

    #*
       Here is some multiline
       comment text
    *#

If you put blank lines around method definitions or loops to
separate them, be aware that the blank lines will be output as is.
To avoid this, make sure the blank lines are enclosed in a comment.
Since you normally have a comment before the next method definition
(right?), you can just extend that comment to include the blank
lines after the previous method definition, like so:

::

    #def method1
    ... lines ...
    #end def
    #*


       Description of method2.
       $arg1, string, a phrase.
    *#
    #def method2($arg1)
    ... lines ...
    #end def

Docstring Comments
------------------


Python modules, classes, and methods can be documented with inline
'documentation strings' (aka 'docstrings'). Docstrings, unlike
comments, are accesible at run-time. Thus, they provide a useful
hook for interactive help utilities.

Cheetah comments can be transformed into doctrings by adding one of
the following prefixes:

::

    ##doc: This text will be added to the method docstring
    #*doc: If your template file is MyTemplate.tmpl, running "cheetah compile"
           on it will produce MyTemplate.py, with a class MyTemplate in it,
           containing a method .respond().  This text will be in the .respond()
           method's docstring. *#

    ##doc-method: This text will also be added to .respond()'s docstring
    #*doc-method: This text will also be added to .respond()'s docstring *#

    ##doc-class: This text will be added to the MyTemplate class docstring
    #*doc-class: This text will be added to the MyTemplate class docstring *#

    ##doc-module: This text will be added to the module docstring MyTemplate.py
    #*doc-module: This text will be added to the module docstring MyTemplate.py*#

Header Comments
---------------

(comments.headers) Cheetah comments can also be transformed into
module header comments using the following syntax:

::

    ##header: This text will be added to the module header comment
    #*header: This text will be added to the module header comment *#

Note the difference between {##doc-module: } and {header: }:
"cheetah-compile" puts {##doc-module: } text inside the module
docstring. {header: } makes the text go { above} the docstring, as
a set of #-prefixed comment lines.


