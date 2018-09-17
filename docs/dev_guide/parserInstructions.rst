Directives: Parser Instructions
===============================


#breakpoint
-----------


The template:

::

    Text before breakpoint.
    #breakpoint
    Text after breakpoint.
    #raise RuntimeError

The output:

::

    Text before breakpoint.

The generated code:

::

    write('Text before breakpoint.\n')

Nothing after the breakpoint was compiled.

#compiler
---------


The template:

::

    // Not a comment
    #compiler commentStartToken = '//'
    // A comment
    #compiler reset
    // Not a comment

The output:

::

    // Not a comment
    // Not a comment

The generated code:

::

    write('// Not a comment\n')
    #  A comment
    write('// Not a comment\n')

So this didn't affect the generated program, it just affected how
the template definition was read.


