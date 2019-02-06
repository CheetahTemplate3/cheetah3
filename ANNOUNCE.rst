Hello!

I'm pleased to announce version 3.2.0, the first stable release of branch
3.2 of CheetahTemplate3.


What's new in CheetahTemplate3
==============================

Features:

  - Dropped support for Python 3.3.
  - Implement LoadTemplate.loadTemplate{Module,Class} to load templates
    from .py[co], .py or .tmpl.
  - CheetahDirOwner caches compiled template in the template directory.
  - CheetahDirOwner now silently ignores errors on compiled templates
    writing. To get tracebacks set CheetahDirOwner.debuglevel = 1.
  - CheetahDirOwner and DirOwner byte-compile compiled templates
    to .pyc/.pyo. Errors on writing are silently ignored.

Minor features:

  - Implement Compiler.__unicode__ under Python 2 and Compiler.__bytes__
    under Python 3.

Bug fixes:

  - Fix a bug in Compiler.__str__: under Python 2 the method now always
    returns str; it encodes unicode to str using encoding from the
    compiled source. Under Python 3 the method decodes bytes to str.

Code:

  - Source code was made flake8-clean using the latest flake8.

Documentation:

  - Remove outdated section markers.
  - Better documentation for ImportHooks.
  - Add an example of a universal makefile.

CI:

  - Run tests with Python 3.7.
  - At travis deploy sdists and wheels for tags.


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
https://pypi.org/project/Cheetah3/3.2.0/

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
