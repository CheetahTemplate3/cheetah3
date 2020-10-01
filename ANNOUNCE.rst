Hello!

I'm pleased to announce version 3.2.6, a bugfix release
of branch 3.2 of CheetahTemplate3.


What's new in CheetahTemplate3
==============================

The contributors for this release are Jonathan Ross Rogers (reported)
and Dale Sedivec (provided a pull request).

Bug fixes:

  - Fixed use of uninitialized variable in _namemapper.


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
https://pypi.org/project/Cheetah3/3.2.6

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
