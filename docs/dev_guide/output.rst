Directives: Output
==================


#echo
-----


The template:

::

    Here is my #echo ', '.join(['silly']*5) # example

The output:

::

    Here is my silly, silly, silly, silly, silly example

The generated code:

::

    write('Here is my ')
    write(filter(', '.join(['silly']*5) ))
    write(' example\n')

#silent
-------


The template:

::

    Here is my #silent ', '.join(['silly']*5) # example

The output:

::

    Here is my  example

The generated code:

::

            write('Here is my ')
            ', '.join(['silly']*5)
            write(' example\n')

OK, it's not quite covert because that extra space gives it away,
but it almost succeeds.

#raw
----


The template:

::

    Text before raw.
    #raw
    Text in raw.  $alligator.  $croc.o['dile'].  #set $a = $b + $c.
    #end raw
    Text after raw.

The output:

::

    Text before raw.
    Text in raw.  $alligator.  $croc.o['dile'].  #set $a = $b + $c.
    Text after raw.

The generated code:

::

            write('''Text before raw.
    Text in raw.  $alligator.  $croc.o['dile'].  #set $a = $b + $c.
    Text after raw.
    ''')

So we see that {#raw} is really like a quoting mechanism. It says
that anything inside it is ordinary text, and Cheetah joins a
{#raw} section with adjacent string literals rather than generating
a separate {write} call.

#include
--------


The main template:

::

    #include "y.tmpl"

The included template y.tmpl:

::

    Let's go $voom!

The shell command and output:

::

    % voom="VOOM" x.py --env
    Let's go VOOM!

The generated code:

::

    write(self._includeCheetahSource("y.tmpl", trans=trans, includeFrom="file",
        raw=0))

#include raw
~~~~~~~~~~~~


The main template:

::

    #include raw "y.tmpl"

The shell command and output:

::

    % voom="VOOM" x.py --env
    Let's go $voom!

The generated code:

::

    write(self._includeCheetahSource("y.tmpl", trans=trans, includeFrom="fil
    e", raw=1))

That last argument, {raw}, makes the difference.

#include from a string or expression (eval)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


The template:

::

    #attr $y = "Let's go $voom!"
    #include source=$y
    #include raw source=$y
    #include source="Bam!  Bam!"

The output:

::

    % voom="VOOM" x.py --env
    Let's go VOOM!Let's go $voom!Bam!  Bam!

The generated code:

::

    write(self._includeCheetahSource(VFS(SL,"y",1), trans=trans,
        includeFrom="str", raw=0, includeID="481020889808.74"))
    write(self._includeCheetahSource(VFS(SL,"y",1), trans=trans,
        includeFrom="str", raw=1, includeID="711020889808.75"))
    write(self._includeCheetahSource("Bam!  Bam!", trans=trans,
        includeFrom="str", raw=0, includeID="1001020889808.75"))

Later in the generated class:

::

    y = "Let's go $voom!"

#slurp
------


The template:

::

    #for $i in range(5)
    $i
    #end for
    #for $i in range(5)
    $i #slurp
    #end for
    Line after slurp.

The output:

::

    0
    1
    2
    3
    4
    0 1 2 3 4 Line after slurp.

The generated code:

::

    for i in range(5):
        write(filter(i)) # generated from '$i' at line 2, col 1.
        write('\n')
    for i in range(5):
        write(filter(i)) # generated from '$i' at line 5, col 1.
        write(' ')
    write('Line after slurp.\n')

The space after each number is because of the space before {#slurp}
in the template definition.

#filter
-------


The template:

::

    #attr $ode = ">> Rubber Ducky, you're the one!  You make bathtime so much fun! <<"
    $ode
    #filter WebSafe
    $ode
    #filter MaxLen
    ${ode, maxlen=13}
    #filter None
    ${ode, maxlen=13}

The output:

::

    >> Rubber Ducky, you're the one!  You make bathtime so much fun! <<
    &gt;&gt; Rubber Ducky, you're the one!  You make bathtime so much fun! &lt;&lt;
    >> Rubber Duc
    >> Rubber Ducky, you're the one!  You make bathtime so much fun! <<

The {WebSafe} filter escapes characters that have a special meaning
in HTML. The {MaxLen} filter chops off values at the specified
length. {#filter None} returns to the default filter, which ignores
the {maxlen} argument.

The generated code:

::

     1  write(filter(VFS(SL,"ode",1))) # generated from '$ode' at line 2, col 1.
     2  write('\n')
     3  filterName = 'WebSafe'
     4  if "WebSafe" in self._filters:
     5      filter = self._currentFilter = self._filters[filterName]
     6  else:
     7      filter = self._currentFilter = \
     8                  self._filters[filterName] = getattr(self._filtersLib,
                           filterName)(self).filter
     9  write(filter(VFS(SL,"ode",1))) # generated from '$ode' at line 4, col 1.
    10  write('\n')
    11  filterName = 'MaxLen'
    12  if "MaxLen" in self._filters:
    13      filter = self._currentFilter = self._filters[filterName]
    14  else:
    15      filter = self._currentFilter = \
    16                  self._filters[filterName] = getattr(self._filtersLib,
                           filterName)(self).filter
    17  write(filter(VFS(SL,"ode",1), maxlen=13)) # generated from
            #'${ode, maxlen=13}' at line 6, col 1.
    18  write('\n')
    19  filter = self._initialFilter
    20  write(filter(VFS(SL,"ode",1), maxlen=13)) # generated from
           #'${ode, maxlen=13}' at line 8, col 1.
    21  write('\n')

As we've seen many times, Cheetah wraps all placeholder lookups in
a {filter} call. (This also applies to non-searchList lookups:
local, global and builtin variables.) The {filter} "function" is
actually an alias to the current filter object:

::

    filter = self._currentFilter

as set at the top of the main method. Here in lines 3-8 and 11-16
we see the filter being changed. Whoops, I lied. {filter} is not an
alias to the filter object itself but to that object's {.filter}
method. Line 19 switches back to the default filter.

In line 17 we see the {maxlen} argument being passed as a keyword
argument to {filter} (not to {VFS}). In line 20 the same thing
happens although the default filter ignores the argument.


