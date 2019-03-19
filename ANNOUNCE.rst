Hello!

I'm pleased to announce version 3.2.1, the first bugfix release of branch
3.2 of CheetahTemplate3.


What's new in CheetahTemplate3
==============================

Contributor for this release is Nicola Soranzo.

Minor features:

  - Changed LoadTemplate.loadTemplate{Module,Class}:
    the loaded module's __name__ set to just the file name.
  - Use imp for Python 2, importlib for Python 3.

Bug fixes:

  - Fix a bug in LoadTemplate.loadTemplate{Module,Class}:
    raise ImportError if the template was not found.

CI:

  - At Travis deploy wheels for macOS.
  - At AppVeyor deploy wheels directly to PyPI.


What is CheetahTemplate3
========================

Cheetah3 is a free and open source template engine.
It's a fork of the original CheetahTemplate library.

Python 2.7 or 3.4+ is required.


Where is CheetahTemplate3
=========================

Site:
http://cheetahtemplate.org/

Development:
https://github.com/CheetahTemplate3

Download:
https://pypi.org/project/Cheetah3/3.2.1/

News and changes:
http://cheetahtemplate.org/news.html

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
