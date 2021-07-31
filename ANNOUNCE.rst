Hello!

I'm pleased to announce version 3.2.7b1, the 1st beta
for minor feature release 3.2.7 of branch 3.2 of CheetahTemplate3.


What's new in CheetahTemplate3
==============================

The contributors for this release are:
N Protokowicz, Enzo Conty, Andrea Mennucci, Saiprasad Kale, odidev.
Many thanks!

Minor features:

  - Load from JSON file to searchlist (similar to loading from pickle).

Bug fixes:

  - Fix ``filetype`` for Python 2 in ``Template``.

Build, CI:

  - Build wheels for ``aarch64`` at Travis; publish them at PyPI.

Tests:

  - ``tox.ini``: Limit ``VIRTUALENV_PIP`` version for Python 3.4.


What is CheetahTemplate3
========================

Cheetah3 is a free and open source template engine.
It's a fork of the original CheetahTemplate library.

Python 2.7 or 3.4+ is required.


Where is CheetahTemplate3
=========================

Site:
https://cheetahtemplate.org/

Development:
https://github.com/CheetahTemplate3

Download:
https://pypi.org/project/Cheetah3/3.2.7b1

News and changes:
https://cheetahtemplate.org/news.html

StackOverflow:
https://stackoverflow.com/questions/tagged/cheetah


Example
=======

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
