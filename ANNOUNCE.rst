Hello!

I'm pleased to announce version 3.3.3, the fourth release
of branch 3.3 of CheetahTemplate3.


What's new in CheetahTemplate3
==============================

Minor features:

  - Protect ``import cgi`` in preparation to Python 3.13.

Tests:

  - Run tests with Python 3.12.

CI:

  - GHActions: Ensure ``pip`` only if needed

    This is to work around a problem in conda with Python 3.7 -
    it brings in wrong version of ``setuptools`` incompatible with Python 3.7.


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
https://pypi.org/project/CT3/3.3.3

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
