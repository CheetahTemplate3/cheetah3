Hello!

I'm pleased to announce version 3.2.6.post1, the 1st post-release
for release 3.2.6 of branch 3.2 of CheetahTemplate3.


What's new in CheetahTemplate3
==============================

Improvement and refactoring in CI and tests with ``tox``.
There were no changes in the main code, there is no need to upgrade
unless you gonna run tests.

The contributors for this release are
Andrew J. Hesford and Victor Stinner.
Many thanks!

This is the first release that provide binary wheels for Python 3.9.

Tests:

   - Add Python 3.9 to ``tox.ini``.

   - Refactor ``tox.ini``.

CI:

  - Run tests with Python 3.9 at Travis and AppVeyor.

  - Run tests for Python 3.4 with ``tox`` under Python 3.5.


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
https://pypi.org/project/Cheetah3/3.2.6.post1

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
