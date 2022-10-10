Hello!

I'm pleased to announce version 3.3.0, the 1st release
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

  - Migrated to GitHub Actions.

    Due to the absent of Python 3.4 at GH Actions tests are not run and
    wheels are not built. Installation from sources should work.

    Due to GH Actions lacking old compilers for w32/w64 releases for old
    Python versions (currently 2.7) are packaged without compiled
    _namemapper.pyd extension. Cheetah can be used without compiled
    _namemapper.pyd extension. A pure-python replacement should work;
    ``Cheetah`` imports it automatically if the compiled extension is
    not available.

  - Stop testing at Travis CI.

  - Stop testing at AppVeyor.


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
https://pypi.org/project/CT3/3.3.0

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
