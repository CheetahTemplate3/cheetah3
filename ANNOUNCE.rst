Hello!

I'm pleased to announce version 3.3.0a1, the 2nd alpha release
of branch 3.3 of CheetahTemplate3.


What's new in CheetahTemplate3
==============================

The contributors for this release are:
N Protokowicz, Enzo Conty, Andrea Mennucci, Saiprasad Kale, odidev,
Pierre Ossman. Many thanks!

Great move:

  - PyPI has wrongfully classified project ``Cheetah3`` as "critical".
    This puts a burden to use 2FA to manage the project at PyPI. To
    avoid the burden the project is renamed to ``CT3`` at PyPI.
    There will be no updates for ``Cheetah3``.
    Sorry for the inconvenience!

Minor features:

  - Use relative imports everywhere.

Tests:

  - Run pure-python ``NameMapper`` tests in a separate process.

  - Fixed a bug in tests with pure-python ``NameMapper``.

  - Add Python 3.10 to ``tox.ini``.

CI:

  - GitHub Actions.

  - Stop testing at Travis CI.

  - Stop testing at AppVeyor.


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
https://pypi.org/project/CT3/3.3.0a1

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
