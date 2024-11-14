Hello!

I'm pleased to announce version 3.4.0b3, the first beta
of release 3.4.0 of branch 3.4 of CheetahTemplate3.


What's new in CheetahTemplate3
==============================

Bug fixes:

  - Fixed ``ImportHooks``: it must raise ``ModuleNotFoundError``
    instead of ``ImportError``.

  - Fixed absolute import in ``ImportHooks`` under Python 3.

  - Fixed ``Template.webInput``: Use ``urllib.parse.parse_qs``
    instead of ``cgi.FieldStorage``; Python 3.13 dropped ``cgi``.

  - Fixed ``_namemapper.c``: Silent an inadvertent ``TypeError`` exception
    in ``PyMapping_HasKeyString`` under Python 3.13+
    caused by ``_namemapper`` looking up a key in a non-dictionary.

  - Fixed ``_namemapper.c``: Silence ``IndexError`` when testing
    ``name[attr]``. Some objects like ``re.MatchObject`` implement both
    attribute access and index access. This confuses ``NameMapper`` because
    it expects ``name[attr]`` to raise ``TypeError`` for objects that don't
    implement mapping protocol.

  - Fixed mapping test in ``NameMapper.py``:
    Python 3.13 brough a new mapping type ``FrameLocalsProxy``.

  - Fixed another ``RecursionError`` in ``ImportHooks`` under PyPy3.

Tests:

  - tox: Run tests under Python 3.13.

CI:

  - CI(GHActions): Switch to ``setup-miniconda``.

  - CI(GHActions): Run tests under Python 3.13.



What is CheetahTemplate3
========================

Cheetah3 is a free and open source (MIT) Python template engine.
It's a fork of the original CheetahTemplate library.

Python 2.7 or 3.4+ is required.


Where is CheetahTemplate3
=========================

Site:
https://cheetahtemplate.org/

Download:
https://pypi.org/project/CT3/3.4.0b3

News and changes:
https://cheetahtemplate.org/news.html

StackOverflow:
https://stackoverflow.com/questions/tagged/cheetah

Mailing lists:
https://sourceforge.net/p/cheetahtemplate/mailman/

Development:
https://github.com/CheetahTemplate3

Developer Guide:
https://cheetahtemplate.org/dev_guide/


Example
=======

Install::

    $ pip install CT3 # (or even "ct3")

Below is a simple example of some Cheetah code, as you can see it's practically
Python. You can import, inherit and define methods just like in a regular Python
module, since that's what your Cheetah templates are compiled to :) ::

    #from Cheetah.Template import Template
    #extends Template

    #set $people = [{'name' : 'Tom', 'mood' : 'Happy'}, {'name' : 'Dick',
                            'mood' : 'Sad'}, {'name' : 'Harry', 'mood' : 'Hairy'}]

    <strong>How are you feeling?</strong>
    <ul>
        #for $person in $people
            <li>
                $person['name'] is $person['mood']
            </li>
        #end for
    </ul>
